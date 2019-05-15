from django.contrib.auth.views import logout_then_login
from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    path('', views.Top.as_view(), name='top'),
    path('done/', views.Done.as_view(), name='done'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', logout_then_login, name='logout'),
    path('user_creation/', views.UserCreation.as_view(), name='user_creation'),
    path('user_creation_complete/<token>/', views.UserCreationComplete.as_view(), name='user_creation_complete'),
    path('user_detail/<int:pk>/', views.UserDetail.as_view(), name='user_detail'),
    path('email_change/', views.EmailChange.as_view(), name='email_change'),
    path('email_change_complete/<token1>/<token2>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
]
