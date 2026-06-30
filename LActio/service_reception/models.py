from django.db import models
from django.contrib.auth.models import AbstractUser



# ===========================модуль для отметки повреждений автомобиля=======================

class CarView(models.Model):
    """Ракурс автомобиля"""
    name = models.CharField(max_length=50)
    image_url = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class DamageType(models.Model):
    """Тип повреждения - выбор из списка"""
    name = models.CharField(max_length=100, verbose_name='Тип повреждения')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Тип повреждения'
        verbose_name_plural = 'Типы повреждений'

class DamageMarker(models.Model):
    """Отметка повреждения"""
    repair_request = models.ForeignKey('RepairRequest', on_delete=models.CASCADE, related_name='damage_markers')
    car_view = models.ForeignKey(CarView, on_delete=models.CASCADE)
    damage_type = models.ForeignKey(DamageType, on_delete=models.SET_NULL, null=True, blank=True)
    
    x = models.FloatField()
    y = models.FloatField()
    
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='damage/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.car_view.name}: {self.damage_type}"



class WorkType(models.Model):
    """Тип работ - выбор из списка"""
    name = models.CharField(max_length=200, verbose_name='Название')
    
    def __str__(self):
        return self.name
    

class User(AbstractUser):
    """Модель пользователя"""
    
    POSITION_CHOICES = [
        ('admin', 'Администратор'),
        ('receptionist', 'Приёмщик'),
        ('master', 'Мастер'),
    ]
    
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, default='receptionist', verbose_name='Должность')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Фото')
    
    # Поле для подтверждения администратором
    is_approved = models.BooleanField(default=False, verbose_name='Подтверждён администратором')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'



class RepairRequest(models.Model):
    # Заявка на приём автомобиля
    
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    

    request_number = models.CharField(max_length=20, unique=True, editable=False)
    receptionist = models.ForeignKey(User, on_delete=models.CASCADE)

    reception_date = models.DateField()
    reception_time = models.TimeField()
    

    client_name = models.CharField(max_length=200)
    client_phone = models.CharField(max_length=20)
    

    car_brand = models.CharField(max_length=100)
    car_model = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=20, blank=True)

    vin = models.CharField(max_length=17, blank=True)
    
    work_types = models.ManyToManyField('WorkType', blank=True)
    
    issue_description = models.TextField()
    notes = models.TextField(blank=True)
    
    # =====Фото приборной панели=====
    dashboard_photo = models.ImageField(
        upload_to='dashboard/', 
        blank=True, 
        null=True, 
        verbose_name='Фото приборной панели'
    )
    
    # =====Пробег=====
    mileage = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='Пробег (км)'
    )


    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # для отчетов
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Время начала")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время завершения")
    time_spent = models.DurationField(null=True, blank=True, verbose_name="Затраченное время")


    def save(self, *args, **kwargs):
        if not self.request_number:
            import uuid
            self.request_number = f"СТО-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.request_number} - {self.client_name}"