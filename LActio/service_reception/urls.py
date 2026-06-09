from django.urls import path
from django.contrib.auth import views as auth_views
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
    path('login/', auth_views.LoginView.as_view(template_name='reception/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('start-inspection/<int:pk>/', views.start_inspection, name='start_inspection'),
    path('complete-request/<int:pk>/', views.complete_request, name='complete_request'),
    path('cancel-request/<int:pk>/', views.cancel_request, name='cancel_request'),
    path('api/requests/<int:request_id>/add-marker/', views.add_damage_marker, name='add_damage_marker'),
]