from django.contrib import admin

from .models import Task, Employee

admin.site.register(Task)
admin.site.register(Employee)
