from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views

from .admin_views import (
    admin_dashboard, admin_users, admin_user_detail, 
    admin_user_change_password, admin_user_approve, admin_user_reject,
    admin_user_make_staff, admin_user_remove_staff, 
    admin_user_toggle_active, admin_requests
)

app_name = 'service_reception'

urlpatterns = [
    path('', views.home, name='home'),
    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/create/', views.request_create, name='request_create'),
    path('requests/<int:pk>/edit/', views.request_update, name='request_update'),
    path('requests/<int:pk>/delete/', views.request_delete, name='request_delete'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('start-inspection/<int:pk>/', views.start_inspection, name='start_inspection'),
    path('complete-request/<int:pk>/', views.complete_request, name='complete_request'),
    path('cancel-request/<int:pk>/', views.cancel_request, name='cancel_request'),
    
    # API для отметок повреждений
    path('api/requests/<int:request_id>/add-marker/', views.add_damage_marker, name='add_damage_marker'),
    path('api/markers/<int:marker_id>/upload-photo/', views.upload_marker_photo, name='upload_marker_photo'),
    path('api/markers/<int:marker_id>/delete/', views.delete_marker, name='delete_marker'),
    
    path('pending-users/', views.pending_users, name='pending_users'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject-user/<int:user_id>/', views.reject_user, name='reject_user'),

    # Админ панель
    path('admin-panel/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', admin_views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/users/<int:user_id>/change-password/', admin_views.admin_user_change_password, name='admin_user_change_password'),
    path('admin-panel/users/<int:user_id>/approve/', admin_views.admin_user_approve, name='admin_user_approve'),
    path('admin-panel/users/<int:user_id>/reject/', admin_views.admin_user_reject, name='admin_user_reject'),
    path('admin-panel/users/<int:user_id>/make-staff/', admin_views.admin_user_make_staff, name='admin_user_make_staff'),
    path('admin-panel/users/<int:user_id>/remove-staff/', admin_views.admin_user_remove_staff, name='admin_user_remove_staff'),
    path('admin-panel/users/<int:user_id>/toggle-active/', admin_views.admin_user_toggle_active, name='admin_user_toggle_active'),
    path('admin-panel/requests/', admin_views.admin_requests, name='admin_requests'),
]