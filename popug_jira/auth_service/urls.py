from django.urls import path

from . import views

app_name = 'auth_service'

urlpatterns = [
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('admin_list', views.admin_list, name='admin_list'),
    path('change/<int:account_id>', views.change_account, name='change'),
    path('change/save', views.save_account_changes, name='save_account_changes')
]
