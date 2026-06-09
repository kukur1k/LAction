from django.urls import path
from . import views

app_name = 'service_reception'

urlpatterns = [
    path('', views.home, name='home'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/edit/', views.request_update, name='request_update'),
    path('requests/<int:pk>/delete/', views.request_delete, name='request_delete'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('register/', views.register, name='register'),
]