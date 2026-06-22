from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, AdminPasswordChangeForm
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, RepairRequest, WorkType, DamageType, CarView, DamageMarker


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Полное управление пользователями"""
    
    change_password_form = AdminPasswordChangeForm
    
    list_display = [
        'username', 
        'get_full_name', 
        'email', 
        'phone', 
        'position', 
        'is_approved', 
        'is_staff',
        'is_active',
    ]
    
    list_filter = [
        'position', 
        'is_approved', 
        'is_staff', 
        'is_active',
        'is_superuser'
    ]
    
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    list_editable = ['is_approved', 'is_staff', 'is_active']
    list_per_page = 20
    readonly_fields = ['last_login', 'date_joined']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('username', 'password')
        }),
        ('Персональные данные', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        ('Должность и роль', {
            'fields': ('position', 'is_approved', 'is_staff', 'is_active', 'is_superuser'),
        }),
        ('Права доступа', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Создание пользователя', {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'phone', 'position', 'password1', 'password2'),
        }),
    )
    
    actions = ['approve_users', 'reject_users', 'make_staff', 'remove_staff', 'make_active', 'make_inactive']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Полное имя'
    get_full_name.admin_order_field = 'first_name'
    
    def approve_users(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} пользователей подтверждено.', messages.SUCCESS)
    approve_users.short_description = 'Подтвердить выбранных пользователей'
    
    def reject_users(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} пользователей отклонено.', messages.WARNING)
    reject_users.short_description = 'Отклонить выбранных пользователей'
    
    def make_staff(self, request, queryset):
        count = queryset.update(is_staff=True)
        self.message_user(request, f'{count} пользователей добавлены в персонал.', messages.SUCCESS)
    make_staff.short_description = 'Сделать персоналом'
    
    def remove_staff(self, request, queryset):
        count = queryset.update(is_staff=False)
        self.message_user(request, f'{count} пользователей убраны из персонала.', messages.WARNING)
    remove_staff.short_description = 'Убрать из персонала'
    
    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} пользователей активировано.', messages.SUCCESS)
    make_active.short_description = 'Активировать пользователей'
    
    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} пользователей деактивировано.', messages.WARNING)
    make_inactive.short_description = 'Деактивировать пользователей'
    
    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('change-password/<int:user_id>/', self.admin_site.admin_view(self.change_password), name='change_user_password'),
        ]
        return custom_urls + urls
    
    def change_password(self, request, user_id):
        user = User.objects.get(pk=user_id)
        if request.method == 'POST':
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f'Пароль пользователя {user.username} изменён')
                return redirect('admin:service_reception_user_change', user_id)
        else:
            form = AdminPasswordChangeForm(user)
        return render(request, 'admin/auth/user/change_password.html', {'form': form, 'user': user})

 
@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    
    list_display = [
        'request_number', 'client_name', 'client_phone', 
        'car_brand', 'car_model', 'license_plate', 
        'reception_date', 'reception_time', 'status', 
        'time_spent',
        'receptionist'
    ]
    list_filter = ['status', 'reception_date', 'receptionist']
    search_fields = ['request_number', 'client_name', 'client_phone', 'license_plate', 'vin']
    readonly_fields = ['request_number']  # убираем started_at, completed_at, time_spent из readonly
    list_editable = ['status']
    list_per_page = 20
    
    fieldsets = (
        ('Номер и статус', {
            'fields': ('request_number', 'status', 'receptionist')
        }),
        ('Дата и время', {
            'fields': ('reception_date', 'reception_time')
        }),
        ('Клиент', {
            'fields': ('client_name', 'client_phone')
        }),
        ('Автомобиль', {
            'fields': ('car_brand', 'car_model', 'license_plate', 'vin', 'mileage')
        }),
        ('Время выполнения', {
            'fields': ('started_at', 'completed_at', 'time_spent'),
            'classes': ('collapse',),
        }),
        ('Фото', {
            'fields': ('dashboard_photo',),
            'classes': ('collapse',)
        }),
        ('Диагностика', {
            'fields': ('work_types', 'issue_description', 'notes')
        }),
    )
    
    actions = ['mark_as_active', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_active(self, request, queryset):
        count = 0
        for req in queryset:
            if req.status == 'draft':
                req.status = 'active'
                req.started_at = timezone.now()
                req.save()
                count += 1
        self.message_user(request, f'{count} заявок переведены в статус "Активна"', messages.SUCCESS)
    mark_as_active.short_description = 'Перевести в статус "Активна"'
    
    def mark_as_completed(self, request, queryset):
        count = 0
        for req in queryset:
            if req.status == 'active':
                req.status = 'completed'
                req.completed_at = timezone.now()
                if req.started_at:
                    req.time_spent = req.completed_at - req.started_at
                req.save()
                count += 1
        self.message_user(request, f'{count} заявок переведены в статус "Завершена"', messages.SUCCESS)
    mark_as_completed.short_description = 'Перевести в статус "Завершена"'
    
    def mark_as_cancelled(self, request, queryset):
        count = queryset.update(status='cancelled')
        self.message_user(request, f'{count} заявок отменены', messages.WARNING)
    mark_as_cancelled.short_description = 'Отменить заявки'


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'id']
    search_fields = ['name']


@admin.register(DamageType)
class DamageTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'id']
    search_fields = ['name']


@admin.register(CarView)
class CarViewAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'image_url']
    list_editable = ['order']
    search_fields = ['name']


@admin.register(DamageMarker)
class DamageMarkerAdmin(admin.ModelAdmin):
    list_display = ['id', 'repair_request', 'car_view', 'damage_type', 'x', 'y']
    list_filter = ['car_view', 'damage_type']
    search_fields = ['repair_request__request_number']