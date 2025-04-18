from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

app_name = 'users'

urlpatterns = [
    # Registro de usuarios
    path('register/', views.register, name='register'),
    
    # Login y logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Gestión de perfil
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/addresses/', views.addresses, name='addresses'),
    path('profile/addresses/add/', views.add_address, name='add_address'),
    path('profile/addresses/edit/<int:pk>/', views.edit_address, name='edit_address'),
    path('profile/addresses/delete/<int:pk>/', views.delete_address, name='delete_address'),
    path('profile/addresses/set-default/<int:pk>/', views.set_default_address, name='set_default_address'),
    
    # Recuperación de contraseña con vistas personalizadas
    path('password-reset/', 
        CustomPasswordResetView.as_view(),
        name='password_reset'),
    path('password-reset/done/', 
        CustomPasswordResetDoneView.as_view(),
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('password-reset-complete/', 
        CustomPasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
]