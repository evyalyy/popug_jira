from django.shortcuts import render
# from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse

from .models import Task, Employee
from .forms import AddTaskForm


def index(request):
    tasks = Task.objects.order_by('-open_date')
    form = AddTaskForm()
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        return HttpResponseServerError('Something went wrong in index')

    return render(request, 'pjira/index.html', {'tasks': tasks, 'form': form})

def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    return render(request, 'pjira/detail.html', {'task': task})


def add_task(request):
    tasks = Task.objects.order_by('-open_date')
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddTaskForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print(form.cleaned_data)
            try:
                emp = Employee.objects.get(name=form.cleaned_data['assignee'])
                new_task = Task(description=form.cleaned_data['description'], assignee=emp)
                new_task.save()
            except Employee.DoesNotExist:
                error_message = 'Employee {} does not exist'.format(form.cleaned_data['assignee'])
                return render(request, 'pjira/index.html', {'tasks': tasks, 'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('pjira:index'))
    else:
        return HttpResponseServerError('Something went wrong in add_task')

    return render(request, 'pjira/index.html', {'tasks': tasks, 'error_message': error_message})
