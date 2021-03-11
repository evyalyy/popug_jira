from django.shortcuts import render

from django.http import HttpResponse, Http404

from .models import Task

from django.template import loader

def index(request):
    tasks = Task.objects.order_by('-open_date')
    return render(request, 'pjira/index.html', {'tasks': tasks})

def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    return render(request, 'pjira/detail.html', {'task': task})
