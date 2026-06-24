from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import csv
from .forms import RepairRequestForm, RepairRequestSearchForm, DamageMarkerForm, CustomUserCreationForm
from .models import RepairRequest, WorkType, DamageMarker, CarView, DamageType, User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from PIL import Image
from django.conf import settings
import os
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q, F, Max, Min
from django.template.loader import get_template
from reportlab.lib.utils import ImageReader


# ========================================Главная================================


def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Админ видит ВСЕ заявки + свои отдельно
            all_requests = RepairRequest.objects.all()
            my_requests = RepairRequest.objects.filter(receptionist=request.user)
            
            total_requests = all_requests.count()
            total_active = all_requests.filter(status='active').count()
            total_completed = all_requests.filter(status='completed').count()
            my_requests_count = my_requests.count()
            recent_requests = all_requests.order_by('-reception_date')[:5]
        else:
            # Обычный пользователь видит ТОЛЬКО свои заявки
            requests = RepairRequest.objects.filter(receptionist=request.user)
            
            total_requests = requests.count()
            total_active = requests.filter(status='active').count()
            total_completed = requests.filter(status='completed').count()
            my_requests_count = total_requests
            recent_requests = requests.order_by('-reception_date')[:5]
    else:
        total_requests = 0
        total_active = 0
        total_completed = 0
        my_requests_count = 0
        recent_requests = []
    
    context = {
        'total_requests': total_requests,
        'total_active': total_active,
        'total_completed': total_completed,
        'my_requests_count': my_requests_count,
        'recent_requests': recent_requests,
    }
    
    return render(request, 'reception/home.html', context)


def request_list(request):
    """Список заявок с поиском"""
    
    if not request.user.is_authenticated:
        return redirect('service_reception:login')
    
    # Проверка - админ ли пользователь
    if request.user.is_staff:
        requests_list = RepairRequest.objects.select_related('receptionist').all().order_by('-reception_date', '-reception_time')
    else:
        requests_list = RepairRequest.objects.filter(receptionist=request.user).select_related('receptionist').order_by('-reception_date', '-reception_time')
    
    form = RepairRequestSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        work_type = form.cleaned_data.get('work_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        car_brand = form.cleaned_data.get('car_brand')
        car_model = form.cleaned_data.get('car_model')
        receptionist_name = form.cleaned_data.get('receptionist_name')
        
        if query:
            requests_list = requests_list.filter(
                Q(request_number__icontains=query) |
                Q(client_name__icontains=query) |
                Q(client_phone__icontains=query) |
                Q(car_brand__icontains=query) |
                Q(car_model__icontains=query) |
                Q(license_plate__icontains=query) |
                Q(vin__icontains=query)
            )
        
        if status:
            requests_list = requests_list.filter(status=status)
        
        if work_type:
            requests_list = requests_list.filter(work_types=work_type)
        
        if date_from:
            requests_list = requests_list.filter(reception_date__gte=date_from)
        
        if date_to:
            requests_list = requests_list.filter(reception_date__lte=date_to)
        
        if car_brand:
            requests_list = requests_list.filter(car_brand__icontains=car_brand)
        
        if car_model:
            requests_list = requests_list.filter(car_model__icontains=car_model)
        
        if receptionist_name and request.user.is_staff:
            # Только админ может искать по приёмщику
            requests_list = requests_list.filter(
                Q(receptionist__first_name__icontains=receptionist_name) |
                Q(receptionist__last_name__icontains=receptionist_name)
            )
    
    context = {
        'requests_list': requests_list,
        'form': form,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'reception/request_list.html', context)


def request_detail(request, pk):
    """Детальная страница заявки"""
    
    repair_request = get_object_or_404(RepairRequest.objects.select_related('receptionist'), pk=pk)
    damage_markers = repair_request.damage_markers.select_related('car_view', 'damage_type').all()
    car_views = CarView.objects.all()
    damage_types = DamageType.objects.all()
    
    context = {
        'repair_request': repair_request,
        'damage_markers': damage_markers,
        'car_views': car_views,
        'damage_types': damage_types,
    }
    return render(request, 'reception/request_detail.html', context)


def request_create(request):
    """Создание новой заявки"""
    
    if request.method == 'POST':
        form = RepairRequestForm(request.POST, request.FILES)
        if form.is_valid():
            repair_request = form.save(commit=False)
            if request.user.is_authenticated:
                repair_request.receptionist = request.user
            repair_request.save()
            form.save_m2m()
            messages.success(request, f'Заявка "{repair_request.request_number}" успешно создана!')
            return redirect('service_reception:request_detail', pk=repair_request.pk)
    else:
        form = RepairRequestForm()
    
    return render(request, 'reception/request_form.html', {'form': form, 'title': 'Создать заявку'})


def request_update(request, pk):
    """Редактирование заявки"""
    
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if request.method == 'POST':
        form = RepairRequestForm(request.POST, request.FILES, instance=repair_request)
        if form.is_valid():
            repair_request = form.save()
            messages.success(request, f'Заявка "{repair_request.request_number}" успешно обновлена!')
            return redirect('service_reception:request_detail', pk=repair_request.pk)
    else:
        form = RepairRequestForm(instance=repair_request)
    
    return render(request, 'reception/request_form.html', {'form': form, 'title': 'Редактировать заявку'})


def request_delete(request, pk):
    """Удаление заявки"""
    
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if request.method == 'POST':
        request_number = repair_request.request_number
        repair_request.delete()
        messages.success(request, f'Заявка "{request_number}" удалена!')
        return redirect('service_reception:request_list')
    
    return render(request, 'reception/request_confirm_delete.html', {'repair_request': repair_request})


@login_required
def start_inspection(request, pk):
    """Начать осмотр автомобиля"""
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if repair_request.status == 'draft':
        repair_request.status = 'active'
        repair_request.started_at = timezone.now()
        repair_request.save()
        messages.success(request, 'Осмотр начат!')
    
    return redirect('service_reception:request_detail', pk=repair_request.pk)


@login_required
def complete_request(request, pk):
    """Завершить заявку"""
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if repair_request.status == 'active':
        repair_request.status = 'completed'
        repair_request.completed_at = timezone.now()
         # общее время работ
        if repair_request.started_at:
            repair_request.time_spent = repair_request.completed_at - repair_request.started_at
        repair_request.save()
        
        messages.success(request, f'Заявка {repair_request.request_number} завершена!')
    else:
        messages.error(request, 'Заявка должна быть в статусе "Активна" для завершения')
    
    return redirect('service_reception:request_list')


@login_required
def cancel_request(request, pk):
    """Отменить заявку"""
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if repair_request.status != 'completed':
        repair_request.status = 'cancelled'
        repair_request.save()
        messages.success(request, f'Заявка {repair_request.request_number} отменена')
    
    return redirect('service_reception:request_list')



def register(request):
    """Регистрация пользователя (ждёт подтверждения админа)"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Пользователь активен, но не подтверждён
            user.is_approved = False  # Ждёт подтверждения
            user.save()
            
            messages.success(request, 'Регистрация отправлена на подтверждение администратору. После одобрения вы сможете войти.')
            return redirect('service_reception:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'reception/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        # Отладка
        print(f"Пользователь: {user}")
        if user:
            print(f"is_approved: {user.is_approved}")
            print(f"Тип is_approved: {type(user.is_approved)}")
        
        if user is not None:
            if user.is_approved == True:  # ← явное сравнение
                login(request, user)
                messages.success(request, 'Вход выполнен')
                return redirect('service_reception:home')
            else:
                messages.error(request, 'Аккаунт не подтверждён. Дождитесь одобрения администратора.')
                return redirect('service_reception:login')
        else:
            messages.error(request, 'Неверный логин или пароль')
            return redirect('service_reception:login')
    
    return render(request, 'reception/login.html')


def is_admin(user):
    return user.is_staff or user.position == 'admin'


@login_required
@user_passes_test(is_admin)
def pending_users(request):
    """Список пользователей, ожидающих подтверждения (только для админа)"""
    pending = User.objects.filter(is_approved=False, is_staff=False)
    return render(request, 'reception/pending_users.html', {'pending_users': pending})


@login_required
@user_passes_test(is_admin)
def approve_user(request, user_id):
    """Подтверждение пользователя админом"""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f'Пользователь {user.username} подтверждён.')
    return redirect('service_reception:pending_users')


@login_required
@user_passes_test(is_admin)
def reject_user(request, user_id):
    """Отклонение пользователя админом"""
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f'Пользователь {username} отклонён и удалён.')
    return redirect('service_reception:pending_users')


@login_required
@csrf_exempt
def add_damage_marker(request, request_id):
    """API: Добавление отметки повреждения"""
    if request.method == 'POST':
        repair_request = get_object_or_404(RepairRequest, id=request_id)
        
        if repair_request.status != 'active':
            return JsonResponse({'success': False, 'error': 'Осмотр не начат'})
        
        try:
            data = json.loads(request.body)
            
            marker = DamageMarker.objects.create(
                repair_request=repair_request,
                car_view_id=data.get('car_view_id'),
                damage_type_id=data.get('damage_type_id'),
                x=data.get('x'),
                y=data.get('y'),
                description=data.get('description', '')
            )
            
            return JsonResponse({
                'success': True,
                'marker_id': marker.id,
                'car_view_id': marker.car_view_id,
                'x': marker.x,
                'y': marker.y
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def upload_marker_photo(request, marker_id):
    """Загрузка фото для отметки повреждения"""
    if request.method == 'POST' and request.FILES.get('photo'):
        marker = get_object_or_404(DamageMarker, id=marker_id)
        marker.photo = request.FILES['photo']
        marker.save()
        return JsonResponse({'success': True, 'photo_url': marker.photo.url})
    return JsonResponse({'success': False, 'error': 'No photo provided'})


@csrf_exempt
def delete_marker(request, marker_id):
    """Удаление отметки повреждения"""
    if request.method == 'DELETE':
        marker = get_object_or_404(DamageMarker, id=marker_id)
        marker.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})




"""Printing"""
@login_required
def print_request_pdf(request, pk):
    """PDF печатная форма заявки через reportlab"""
    repair_request = get_object_or_404(RepairRequest.objects.select_related('receptionist'), pk=pk)
    damage_markers = repair_request.damage_markers.select_related('car_view', 'damage_type').all()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="заявка_{repair_request.request_number}.pdf"'
    
    # Создание PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    
      # ===== русский шрифт =====
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os
    
    font_path = "/app/fonts/arialmt.ttf"
    
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'
    

    def add_photo(p, image_field, x, y, max_width=80*mm, max_height=60*mm):
        """Вставить фото в PDF"""
        if not image_field or not image_field.name:
            return None
        
        try:
        
            img_path = os.path.join(settings.MEDIA_ROOT, image_field.name)
            
            if not os.path.exists(img_path):
                return None
            
            img = Image.open(img_path)
            
            img_width, img_height = img.size
            
            scale_x = max_width / img_width
            scale_y = max_height / img_height
            scale = min(scale_x, scale_y)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            img_reader = ImageReader(img)
            p.drawImage(img_reader, x, y - new_height, width=new_width, height=new_height)
            
            return new_height
        except Exception as e:
            return None
    
    
    # ===== Заголовок =====
    p.setFont(font_name, 18)
    p.drawString(30*mm, height - 30*mm, "-АКТ ПРИЁМКИ АВТОМОБИЛЯ-")
    
    p.setFont(font_name, 14)
    p.drawString(30*mm, height - 45*mm, f"Заявка № {repair_request.request_number}")
    
    # Линия
    p.line(30*mm, height - 50*mm, 180*mm, height - 50*mm)
    
    # ===== Информация о клиенте =====
    y = height - 65*mm
    p.setFont(font_name, 12)
    p.drawString(30*mm, y, "1. ИНФОРМАЦИЯ О КЛИЕНТЕ")
    y -= 8*mm
    
    p.setFont(font_name, 10)
    p.drawString(30*mm, y, f"Клиент: {repair_request.client_name}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Телефон: {repair_request.client_phone}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Дата приёма: {repair_request.reception_date.strftime('%d.%m.%Y')}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Время: {repair_request.reception_time.strftime('%H:%M')}")
    y -= 10*mm
    
    # ===== Информация об автомобиле =====
    p.setFont(font_name, 12)
    p.drawString(30*mm, y, "2. ИНФОРМАЦИЯ ОБ АВТОМОБИЛЕ")
    y -= 8*mm
    
    p.setFont(font_name, 10)
    p.drawString(30*mm, y, f"Марка: {repair_request.car_brand}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Модель: {repair_request.car_model}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Гос номер: {repair_request.license_plate}")
    y -= 6*mm
    p.drawString(30*mm, y, f"VIN: {repair_request.vin or '-'}")
    y -= 6*mm
    p.drawString(30*mm, y, f"Пробег: {repair_request.mileage or '-'} км")
    y -= 6*mm
    
    # Фото приборной панели
    if repair_request.dashboard_photo:
        p.drawString(30*mm, y, "Фото приборной панели:")
        y -= 5*mm
        add_photo(p, repair_request.dashboard_photo, 30*mm, y, max_width=70*mm, max_height=50*mm)
        y -= 55*mm
    
    y -= 5*mm
    
    # ===== Причина обращения =====
    p.setFont(font_name, 12)
    p.drawString(30*mm, y, "3. ПРИЧИНА ОБРАЩЕНИЯ")
    y -= 8*mm
    
    p.setFont(font_name, 10)
    # Переносим длинный текст
    text = repair_request.issue_description
    lines = []
    if len(text) > 60:
        words = text.split()
        line = ""
        for w in words:
            if len(line + w) < 60:
                line += w + " "
            else:
                lines.append(line.strip())
                line = w + " "
        if line:
            lines.append(line.strip())
    else:
        lines = [text]
    
    for line in lines:
        p.drawString(30*mm, y, line)
        y -= 6*mm
    
    if repair_request.notes:
        p.drawString(30*mm, y, f"Примечания: {repair_request.notes}")
        y -= 8*mm
    
    y -= 5*mm
    
    # ===== Типы работ =====
    p.setFont(font_name, 12)
    p.drawString(30*mm, y, "4. ТИПЫ РАБОТ")
    y -= 8*mm
    
    p.setFont(font_name, 10)
    work_types = [wt.name for wt in repair_request.work_types.all()]
    if work_types:
        p.drawString(30*mm, y, ", ".join(work_types))
    else:
        p.drawString(30*mm, y, "Не указаны")
    y -= 10*mm
    
    # ===== Повреждения =====
    p.setFont(font_name, 12)
    p.drawString(30*mm, y, "5. ОТМЕЧЕННЫЕ ПОВРЕЖДЕНИЯ")
    y -= 8*mm
    
    if damage_markers:
        for marker in damage_markers:
            p.setFont(font_name, 10)
            p.drawString(30*mm, y, f"• {marker.car_view.name}")
            y -= 5*mm
            p.setFont(font_name, 9)
            if marker.damage_type:
                p.drawString(35*mm, y, f"Тип: {marker.damage_type.name}")
                y -= 4*mm
            if marker.description:
                p.drawString(35*mm, y, f"Описание: {marker.description}")
                y -= 4*mm
            
            # Фото повреждения
            if marker.photo:
                y -= 2*mm
                add_photo(p, marker.photo, 35*mm, y, max_width=60*mm, max_height=40*mm)
                y -= 45*mm
            
            y -= 3*mm
            
            # Если заканчивается страница
            if y < 30*mm:
                p.showPage()
                y = height - 20*mm
    else:
        p.setFont(font_name, 10)
        p.drawString(30*mm, y, "Повреждений не отмечено")
        y -= 8*mm
    
    # ===== Подписи =====
    y -= 15*mm
    if y < 50*mm:
        p.showPage()
        y = height - 30*mm
    
    p.line(30*mm, y, 80*mm, y)
    p.setFont(font_name, 9)
    p.drawString(30*mm, y + 3*mm, f"Приёмщик: {repair_request.receptionist.get_full_name() or repair_request.receptionist.username}")
    
    p.line(120*mm, y, 180*mm, y)
    p.drawString(120*mm, y + 3*mm, f"Дата: {repair_request.reception_date.strftime('%d.%m.%Y')}")
    
    # ===== Футер =====
    p.setFont(font_name, 8)
    p.drawString(30*mm, 15*mm, f"Документ сформирован {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    p.drawString(130*mm, 15*mm, "СТО Приёмка")
    
    p.showPage()
    p.save()
    
    return response




def format_duration(value):
    if not value or value == "—":
        return "—"
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}ч {minutes}м"
    elif minutes > 0:
        return f"{minutes}м {seconds}с"
    else:
        return f"{seconds}с"




@login_required
@user_passes_test(lambda u: u.is_staff)
def reports_receptionists(request):
    
    # Получаем всех приемщиков
    receptionists = User.objects.filter(
        repairrequest__isnull=False
    ).distinct().annotate(
        total_requests=Count('repairrequest'),
        completed_requests=Count('repairrequest', filter=Q(repairrequest__status='completed')),
        active_requests=Count('repairrequest', filter=Q(repairrequest__status='active')),
        avg_time=Avg('repairrequest__time_spent'),
        min_time=Min('repairrequest__time_spent'),
        max_time=Max('repairrequest__time_spent'),
        total_time=Sum('repairrequest__time_spent'),
    )
    
    # заявки для каждого приемщика
    receptionist_data = []
    for r in receptionists:
        # Заявки приемщика
        requests = RepairRequest.objects.filter(
            receptionist=r
        ).order_by('-reception_date')
        

        for req in requests:
            req.time_spent_formatted = format_duration(req.time_spent)


        receptionist_data.append({
            'user': r,
            'stats': {
                'total': r.total_requests,
                'completed': r.completed_requests,
                'active': r.active_requests,
                'avg_time': format_duration(r.avg_time),
                'min_time': format_duration(r.min_time),
                'max_time': format_duration(r.max_time),
                'total_time': format_duration(r.total_time),
            },
            'requests': requests,
        })
    
    context = {
        'receptionist_data': receptionist_data,
    }
    
    return render(request, 'reception/reports_receptionists.html', context)







# добавление печати
def add_stamp(p, width, height):
    
    try:
        p.saveState()
        
        stamp_path = "static/images/stamp.png"

        # Шрифт
        font_path = "/app/fonts/arialmt.ttf"
        try:
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            font_name = 'Arial'
        except:
            font_name = 'Helvetica'
        
        if os.path.exists(stamp_path):
            img = ImageReader(stamp_path)
            stamp_width = 80*mm
            stamp_height = 40*mm
            x = (width - stamp_width) / 2
            y = (height - stamp_height) / 2
            p.drawImage(img, x, y, width=stamp_width, height=stamp_height, mask='auto')
        else:
        #    иначе текстовый
            p.setFont(font_name, 50)
            p.setFillColorRGB(0.6, 0.6, 0.6, alpha=0.15)
            p.translate(width/1.5, height/1.5)
            p.rotate(-45)
            p.drawString(-70, 0, "ООО Л-АВТО")
        
        p.restoreState()
    except Exception as e:
        print(f"Stamp error: {e}")
        pass


@login_required
def reports_receptionists_pdf(request):
    
    # Получаем данные
    receptionists = User.objects.filter(
        repairrequest__isnull=False
    ).distinct().annotate(
        total_requests=Count('repairrequest'),
        completed_requests=Count('repairrequest', filter=Q(repairrequest__status='completed')),
        active_requests=Count('repairrequest', filter=Q(repairrequest__status='active')),
        avg_time=Avg('repairrequest__time_spent'),
        min_time=Min('repairrequest__time_spent'),
        max_time=Max('repairrequest__time_spent'),
        total_time=Sum('repairrequest__time_spent'),
    )
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="otchet_po_priemshikam.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    # Шрифт
    font_path = "/app/fonts/arialmt.ttf"
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'
     
    # ===== Заголовок =====
    y = height - 30*mm
    p.setFont(font_name, 16)
    p.drawString(30*mm, y, "ОТЧЕТ ПО ПРИЕМЩИКАМ")
    
    p.setFont(font_name, 10)
    p.drawString(30*mm, y - 10*mm, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # ===== Заголовки таблицы =====
    y -= 25*mm
    p.setFont(font_name, 10)
    p.drawString(30*mm, y, "Приемщик")
    p.drawString(80*mm, y, "Заявок")
    p.drawString(110*mm, y, "Завершено")
    p.drawString(140*mm, y, "В работе")
    p.drawString(170*mm, y, "Среднее")
    
    y -= 5*mm
    p.line(30*mm, y, 210*mm, y)
    y -= 5*mm
    
    # ===== Данные по приемщикам =====
    if receptionists.exists():
        p.setFont(font_name, 9)
        for r in receptionists:
            if y < 30*mm:
                p.showPage()
                y = height - 30*mm
                p.setFont(font_name, 9)
            
            name = r.get_full_name() or r.username
            avg = format_duration(r.avg_time)
            total = format_duration(r.total_time)
            
            p.drawString(30*mm, y, name[:20])
            p.drawString(80*mm, y, str(r.total_requests))
            p.drawString(110*mm, y, str(r.completed_requests))
            p.drawString(140*mm, y, str(r.active_requests or 0))
            p.drawString(170*mm, y, avg)
            
            y -= 8*mm
            
            # ===== Подтаблица с заявками приемщика =====
            requests = RepairRequest.objects.filter(receptionist=r).order_by('-reception_date')[:10]
            if requests.exists():
                p.setFont(font_name, 8)
                p.drawString(35*mm, y, "Заявки:")
                y -= 5*mm
                
                p.setFont(font_name, 7)
                p.drawString(35*mm, y, "№")
                p.drawString(55*mm, y, "Клиент")
                p.drawString(100*mm, y, "Авто")
                p.drawString(140*mm, y, "Статус")
                p.drawString(175*mm, y, "Время")
                y -= 4*mm
                
                p.setFont(font_name, 7)
                for req in requests:
                    if y < 30*mm:
                        p.showPage()
                        y = height - 30*mm
                        p.setFont(font_name, 7)
                    
                    time_str = format_duration(req.time_spent)
                    if req.status == 'active':
                        time_str = "В процессе"
                    
                    p.drawString(35*mm, y, req.request_number[:10])
                    p.drawString(55*mm, y, req.client_name[:15])
                    p.drawString(100*mm, y, f"{req.car_brand[:10]} {req.car_model[:10]}")
                    p.drawString(140*mm, y, req.get_status_display())
                    p.drawString(175*mm, y, time_str)
                    
                    y -= 4*mm
                
                y -= 3*mm
                p.setFont(font_name, 9)
    else:
        p.setFont(font_name, 12)
        p.drawString(30*mm, y, "Нет данных о приемщиках")


        # ===== Подписи =====
      
        
    y -= 5*mm    
    p.line(120*mm, y, 180*mm, y)
    p.drawString(120*mm, y + 3*mm, f"Дата: {datetime.now().strftime('%d.%m.%Y')}")
    

    add_stamp(p, width, height)

    p.showPage()
    p.save()
    
    return response




def export_requests_csv_all(request):
    """экспорт заявок в CSV"""
    

    requests = RepairRequest.objects.all().select_related('receptionist')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename=export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    )
    
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    writer.writerow([
        '№ заявки',
        'Дата приема',
        'Клиент',
        'Телефон',
        'Марка',
        'Модель',
        'Госномер',
        'VIN',
        'Описание проблем',
        'Статус',
        'Приемщик',
        'Время завершения',
        'Время выполнения',
        'Заказ-наряд',
        'Итоговая стоимость'
    ])
    

    for req in requests:
        writer.writerow([
            req.request_number,
            req.reception_date.strftime('%d.%m.%Y') if req.reception_date else '',
            req.client_name,
            req.client_phone or '',
            req.car_brand,
            req.car_model,
            req.license_plate or '',
            req.vin or '',
            req.issue_description or '',
            req.get_status_display(),
            req.receptionist.get_full_name() if req.receptionist else '',
            str(req.completed_at) if req.completed_at else '',
            str(req.time_spent) if req.time_spent else '',
            '',  # Заказ-наряд 
            '',  # Итоговая стоимость
        ])
    
    return response

def export_request_csv(request, request_id):
    """экспорт заявки в CSV"""

    req = get_object_or_404(RepairRequest, id=request_id)
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename=export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv'
    )
    
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    writer.writerow([
        '№ заявки',
        'Дата приема',
        'Клиент',
        'Телефон',
        'Марка',
        'Модель',
        'Госномер',
        'VIN',
        'Описание проблем',
        'Статус',
        'Приемщик',
        'Время завершения',
        'Время выполнения',
        'Заказ-наряд',
        'Итоговая стоимость'
    ])
    


    writer.writerow([
        req.request_number,
        req.reception_date.strftime('%d.%m.%Y') if req.reception_date else '',
        req.client_name,
        req.client_phone or '',
        req.car_brand,
        req.car_model,
        req.license_plate or '',
        req.vin or '',
        req.issue_description or '',
        req.get_status_display(),
        req.receptionist.get_full_name() if req.receptionist else '',
        str(req.completed_at) if req.completed_at else '',
        str(req.time_spent) if req.time_spent else '',
        '',  # Заказ-наряд 
        '',  # Итоговая стоимость
    ])
    
    return response