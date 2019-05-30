from django.contrib.auth.views import logout_then_login
from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    path('', views.Top.as_view(), name='top'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', logout_then_login, name='logout'),
    path('user_create/', views.UserCreate.as_view(), name='user_create'),
    path('user_create_complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    path('user_detail/<int:pk>/', views.UserDetail.as_view(), name='user_detail'),
    path('user_delete/<int:pk>/', views.UserDelete.as_view(), name='user_delete'),
    path('email_change/', views.EmailChange.as_view(), name='email_change'),
    path('email_change_complete/<token1>/<token2>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('done/', views.Done.as_view(), name='done'),
    path('category_list/', views.CategoryList.as_view(), name='category_list'),
    path('category_create/', views.CategoryCreate.as_view(), name='category_create'),
    path('category_update/<int:pk>/', views.CategoryUpdate.as_view(), name='category_update'),
    path('category_delete/<int:pk>/', views.CategoryDelete.as_view(), name='category_delete'),
    path('item_list/', views.ItemList.as_view(), name='item_list'),
    path('item_create/', views.ItemCreate.as_view(), name='item_create'),
    path('item_update/<int:pk>/', views.ItemUpdate.as_view(), name='item_update'),
    path('item_delete/<int:pk>/', views.ItemDelete.as_view(), name='item_delete'),
]
