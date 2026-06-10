from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from .models import User, RepairRequest, WorkType, DamageType
from .forms import UserAdminForm, RepairRequestAdminForm
from .forms import AdminSetPasswordForm

def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Дашборд администратора"""
    total_users = User.objects.count()
    total_requests = RepairRequest.objects.count()
    pending_users = User.objects.filter(is_approved=False, is_staff=False).count()
    active_requests = RepairRequest.objects.filter(status='active').count()
    
    context = {
        'total_users': total_users,
        'total_requests': total_requests,
        'pending_users': pending_users,
        'active_requests': active_requests,
    }
    return render(request, 'reception/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Управление пользователями"""
    users = User.objects.all().order_by('-date_joined')
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    context = {'users': users, 'search': search}
    return render(request, 'reception/admin/users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """Просмотр и редактирование пользователя"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserAdminForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные пользователя {user.username} обновлены')
            return redirect('service_reception:admin_users')
    else:
        form = UserAdminForm(instance=user)
    
    context = {'user_obj': user, 'form': form}
    return render(request, 'reception/admin/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_change_password(request, user_id):
    """Смена пароля пользователя админом"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Пароль пользователя {user.username} изменён')
            return redirect('service_reception:admin_users')
    else:
        form = PasswordChangeForm(user)
    
    context = {'form': form, 'user_obj': user}
    return render(request, 'reception/admin/change_password.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_approve(request, user_id):
    """Подтверждение пользователя"""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.save()
    messages.success(request, f'Пользователь {user.username} подтверждён')
    return redirect(request.META.get('HTTP_REFERER', 'service_reception:admin_users'))


@login_required
@user_passes_test(is_admin)
def admin_user_reject(request, user_id):
    """Отклонение пользователя"""
    user = get_object_or_404(User, id=user_id)
    user.is_approved = False
    user.save()
    messages.warning(request, f'Пользователь {user.username} отклонён')
    return redirect(request.META.get('HTTP_REFERER', 'service_reception:admin_users'))


@login_required
@user_passes_test(is_admin)
def admin_user_make_staff(request, user_id):
    """Сделать пользователя персоналом"""
    user = get_object_or_404(User, id=user_id)
    user.is_staff = True
    user.save()
    messages.success(request, f'Пользователь {user.username} теперь в персонале')
    return redirect(request.META.get('HTTP_REFERER', 'service_reception:admin_users'))


@login_required
@user_passes_test(is_admin)
def admin_user_remove_staff(request, user_id):
    """Убрать пользователя из персонала"""
    user = get_object_or_404(User, id=user_id)
    user.is_staff = False
    user.save()
    messages.warning(request, f'Пользователь {user.username} убран из персонала')
    return redirect(request.META.get('HTTP_REFERER', 'service_reception:admin_users'))


@login_required
@user_passes_test(is_admin)
def admin_user_toggle_active(request, user_id):
    """Активировать/деактивировать пользователя"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = 'активирован' if user.is_active else 'деактивирован'
    messages.success(request, f'Пользователь {user.username} {status}')
    return redirect(request.META.get('HTTP_REFERER', 'service_reception:admin_users'))


@login_required
@user_passes_test(is_admin)
def admin_requests(request):
    """Все заявки для админа"""
    requests_list = RepairRequest.objects.all().order_by('-reception_date', '-reception_time')
    
    search = request.GET.get('search')
    if search:
        requests_list = requests_list.filter(
            Q(request_number__icontains=search) |
            Q(client_name__icontains=search) |
            Q(license_plate__icontains=search)
        )
    
    context = {'requests_list': requests_list, 'search': search}
    return render(request, 'reception/admin/requests.html', context)



def admin_user_change_password(request, user_id):
    """Смена пароля пользователя админом (без старого пароля)"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            form.save(user_obj)
            messages.success(request, f'Пароль пользователя {user_obj.username} изменён')
            return redirect('service_reception:admin_users')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = AdminSetPasswordForm()
    
    context = {'form': form, 'user_obj': user_obj}
    return render(request, 'reception/admin/change_password.html', context)