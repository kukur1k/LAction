from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, RepairRequest, WorkType, DamageType, CarView, DamageMarker


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'position', 'is_approved', 'is_staff']
    list_filter = ['position', 'is_approved', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'position', 'avatar', 'is_approved'),  # ← добавьте is_approved
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'position', 'is_approved'),  # ← добавьте is_approved
        }),
    )


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


class DamageMarkerInline(admin.TabularInline):
    model = DamageMarker
    extra = 1
    fields = ['car_view', 'damage_type', 'x', 'y', 'description', 'photo']


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'client_name', 'client_phone', 
        'car_brand', 'car_model', 'license_plate', 
        'reception_date', 'reception_time', 'status'
    ]
    list_filter = ['status', 'reception_date']
    search_fields = [
        'request_number', 'client_name', 'client_phone', 
        'car_brand', 'car_model', 'license_plate', 'vin'
    ]
    readonly_fields = ['request_number']  # ← только request_number
    
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
        ('Диагностика', {
            'fields': ('work_types', 'issue_description', 'notes')
        }),
    )
    
    inlines = [DamageMarkerInline]


@admin.register(DamageMarker)
class DamageMarkerAdmin(admin.ModelAdmin):
    list_display = ['id', 'repair_request', 'car_view', 'damage_type', 'x', 'y']
    list_filter = ['car_view', 'damage_type']
    search_fields = ['repair_request__request_number']