# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # 认证相关
    path('register/', views.register, name='register'),
    path('send-captcha/', views.send_email_captcha, name='send_email_captcha'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.logout, name='logout'),

    # 密码重置
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    # 用户资料
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/<str:username>/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('settings/', views.profile_settings, name='settings'),
    path('change-password/', views.change_password, name='change_password'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
]