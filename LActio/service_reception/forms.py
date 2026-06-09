from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, RepairRequest, WorkType, DamageMarker, CarView, DamageType
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
# ==========форма для пользователей==========

class UserRegistrationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя (приёмщика)
    """
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'position', 'password1', 'password2']
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Логин'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фамилия'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (***) ***-**-**)'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Должность'
            }),
        }


class UserProfileForm(forms.ModelForm):
    """
    Форма редактирования профиля пользователя
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'avatar']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фамилия'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Телефон'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Должность'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


# ==========формы для заявок==========

class RepairRequestForm(forms.ModelForm):
    """
    Форма создания заявки на приём автомобиля
    """
    class Meta:
        model = RepairRequest
        fields = [
            'reception_date', 'reception_time',
            'client_name', 'client_phone',
            'car_brand', 'car_model', 'license_plate', 'vin',
            'mileage', 'dashboard_photo',
            'work_types', 'issue_description', 'notes', 
        ]
        
        widgets = {
            'reception_date': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Дата приёма',
                'type': 'date'
            }),
            'reception_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'placeholder': 'Время приёма',
                'type': 'time'
            }),
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иванов Иван Иванович'
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'car_brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Toyota'
            }),
            'car_model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Camry'
            }),
            'license_plate': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'А123ВС77'
            }),
            'vin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'JHMGD38408S123456'
            }),
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пробег в км'
            }),
            'dashboard_photo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'work_types': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите типы работ'
            }),
            'issue_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишите причину обращения...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Дополнительные примечания...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vin'].required = False
        self.fields['mileage'].required = False
        self.fields['dashboard_photo'].required = False
        self.fields['work_types'].required = False



def update_status(request, pk):
    """Обновление статуса заявки"""
    repair_request = get_object_or_404(RepairRequest, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(RepairRequest.STATUS_CHOICES):
            repair_request.status = new_status
            repair_request.save()
            messages.success(request, f'Статус изменён на "{repair_request.get_status_display()}"')
    
    return redirect('service_reception:request_detail', pk=repair_request.pk)


# ==========формы для отметок повреждений==========

class DamageMarkerForm(forms.ModelForm):
    """
    Форма для добавления отметки повреждения на карте автомобиля
    """
    class Meta:
        model = DamageMarker
        fields = ['car_view', 'damage_type', 'x', 'y', 'description', 'photo']
        
        widgets = {
            'car_view': forms.Select(attrs={
                'class': 'form-control'
            }),
            'damage_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'x': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'X координата (0-100)',
                'step': '0.1'
            }),
            'y': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Y координата (0-100)',
                'step': '0.1'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Царапина на бампере'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class DamageMarkerQuickForm(forms.ModelForm):
    """
    Упрощённая форма для быстрого добавления отметки (координаты из JS)
    """
    class Meta:
        model = DamageMarker
        fields = ['damage_type', 'description', 'photo']
        
        widgets = {
            'damage_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Описание повреждения'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


# ==========формы для справочников==========

class WorkTypeForm(forms.ModelForm):
    """
    Форма для добавления/редактирования типа работ
    """
    class Meta:
        model = WorkType
        fields = ['name']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Диагностика, Ремонт, Осмотр'
            }),
        }


class DamageTypeForm(forms.ModelForm):
    """
    Форма для добавления/редактирования типа повреждения
    """
    class Meta:
        model = DamageType
        fields = ['name']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Царапина, Вмятина, Скол'
            }),
        }


class CarViewForm(forms.ModelForm):
    """
    Форма для добавления/редактирования ракурса автомобиля
    """
    class Meta:
        model = CarView
        fields = ['name', 'image_url', 'order']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Вид спереди'
            }),
            'image_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/static/images/car_front.svg'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Порядок отображения'
            }),
        }


class RepairRequestSearchForm(forms.Form):
    """
    Форма поиска заявок
    """
    # Поиск по тексту
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Номер заявки, клиент, телефон, гос номер, VIN...'
        })
    )
    
    # Фильтры
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Все статусы')] + RepairRequest.STATUS_CHOICES,
        label='Статус',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    work_type = forms.ModelChoiceField(
        queryset=WorkType.objects.all(),
        required=False,
        label='Тип работ',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Диапазон дат
    date_from = forms.DateField(
        required=False,
        label='Дата с',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Дата по',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Марка и модель
    car_brand = forms.CharField(
        required=False,
        label='Марка',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Toyota, BMW, Mercedes...'
        })
    )
    
    car_model = forms.CharField(
        required=False,
        label='Модель',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Camry, X5, S-Class...'
        })
    )
    
    # Приёмщик (поиск по имени или фамилии)
    receptionist_name = forms.CharField(
        required=False,
        label='Приёмщик',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Имя или фамилия приёмщика'
        })
    )


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с кастомной моделью User"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'position')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'search_field_input'


class CustomUserChangeForm(UserChangeForm):
    """Форма редактирования пользователя"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'position', 'avatar')