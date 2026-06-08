from django.db import models


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