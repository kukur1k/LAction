from django.shortcuts import render
from .forms import RepairRequestForm, RepairRequestSearchForm, DamageMarkerForm
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from .models import RepairRequest, WorkType, DamageMarker, CarView, DamageType, User
from django.contrib.auth.decorators import login_required


# ========================================Главная================================


def home(request):
    """Главная страница с дашбордом"""
    
    # Подсчет количества записей
    total_requests = RepairRequest.objects.count()
    total_active = RepairRequest.objects.filter(status='active').count()
    total_completed = RepairRequest.objects.filter(status='completed').count()
    
    # Последние 5 заявок
    recent_requests = RepairRequest.objects.all().order_by('-reception_date')[:5]
    
    # Статистика по типам работ
    work_types_stats = []
    for wt in WorkType.objects.all():
        count = RepairRequest.objects.filter(work_types=wt).count()
        if count > 0:
            work_types_stats.append({'name': wt.name, 'count': count})
    
    context = {
        'total_requests': total_requests,
        'total_active': total_active,
        'total_completed': total_completed,
        'recent_requests': recent_requests,
        'work_types_stats': work_types_stats,
    }
    
    # Если пользователь авторизован - добавляем его заявки
    if request.user.is_authenticated:
        context['my_requests_count'] = RepairRequest.objects.filter(receptionist=request.user).count()
        context['my_active_count'] = RepairRequest.objects.filter(receptionist=request.user, status='active').count()
    
    return render(request, 'reception/home.html', context)


# ========================================Заявки================================


def request_list(request):
    """Список заявок с поиском"""
    
    requests_list = RepairRequest.objects.select_related('receptionist').all().order_by('-reception_date', '-reception_time')
    
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
        
        if receptionist_name:
            requests_list = requests_list.filter(
                Q(receptionist__first_name__icontains=receptionist_name) |
                Q(receptionist__last_name__icontains=receptionist_name)
            )
    
    context = {
        'requests_list': requests_list,
        'form': form,
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
            repair_request.receptionist = request.user if request.user.is_authenticated else None
            repair_request.save()
            form.save_m2m()  # Сохраняем ManyToMany (work_types)
            messages.success(request, f'Заявка "{repair_request.request_number}" успешно создана!')
            return redirect('reception:request_detail', pk=repair_request.pk)
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
            return redirect('reception:request_detail', pk=repair_request.pk)
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
        return redirect('reception:request_list')
    
    return render(request, 'reception/request_confirm_delete.html', {'repair_request': repair_request})

@login_required
def my_requests(request):
    """Мои заявки (только текущего пользователя)"""
    requests_list = RepairRequest.objects.filter(
        receptionist=request.user
    ).order_by('-reception_date', '-reception_time')
    
    query = request.GET.get('q')
    if query:
        requests_list = requests_list.filter(
            Q(request_number__icontains=query) |
            Q(client_name__icontains=query) |
            Q(license_plate__icontains=query)
        )
    
    context = {
        'requests_list': requests_list,
        'query': query,
    }
    return render(request, 'service_reception/my_requests.html', context)

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('service_reception:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})