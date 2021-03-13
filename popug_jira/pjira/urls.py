from django.urls import path

from . import views

app_name = 'pjira'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:task_id>/', views.detail, name='detail'),
    path('add/', views.add_task, name='add_task'),
    path('close/<int:task_id>', views.close_task, name='close_task')
]
