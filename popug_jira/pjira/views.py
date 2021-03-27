from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings

from .models import Task, Employee, TaskStatus
from .forms import AddTaskForm
from auth_service.models import Role

from common.authorized_only import authorized_only
from common.event_utils import send_event, consume_events
from common.events.business import TaskCreatedBE, TaskAssignedBE, TaskClosedBE
from common.events.cud import AccountCreatedCUDv2, AccountChangedCUDv2
from common.schema_registry import SchemaRegistry
from .event_handlers import *

import random
import requests
import jwt
import json
import threading
from kafka import KafkaProducer, KafkaConsumer


registry = SchemaRegistry()
registry.register(2, AccountCreatedCUDv2, AccountCreatedHandlerV2)
registry.register(2, AccountChangedCUDv2, AccountChangedHandlerV2)

registry.register(1, TaskCreatedBE)
registry.register(1, TaskAssignedBE)
registry.register(1, TaskClosedBE)


producer = KafkaProducer(client_id='pjira_tasks',
                        bootstrap_servers=[settings.KAFKA_HOST],
                        value_serializer=lambda m: json.dumps(m).encode('ascii'))

accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])


thr = threading.Thread(target=consume_events, args=(accounts_consumer, registry, 'pjira'))
thr.start()


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def index(request):
    open_tasks = Task.objects.filter(status=TaskStatus.OPEN).order_by('-open_date')
    closed_tasks = Task.objects.filter(status=TaskStatus.CLOSED).order_by('-open_date')
    employees = Employee.objects.all()
    return render(request, 'pjira/index.html', {'open_tasks': open_tasks, 'closed_tasks': closed_tasks, 'employees': employees})


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    return render(request, 'pjira/detail.html', {'task': task})


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def add_task(request):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddTaskForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print(form.cleaned_data)
            try:
                # emp = Employee.objects.get(name=form.cleaned_data['assignee'])
                new_task = Task(description=form.cleaned_data['description'])
                new_task.save()
                send_event(producer, 'tasks', registry, 1, TaskCreatedBE(task_id=new_task.id, description=new_task.description))
            except Employee.DoesNotExist:
                error_message = 'Employee {} does not exist'.format(form.cleaned_data['assignee'])
                return render(request, 'pjira/add_task.html', {'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('pjira:index'))
    else:
        form = AddTaskForm()

    return render(request, 'pjira/add_task.html', {'form': form, 'error_message': error_message})


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def close_task(request, task_id):
    if request.method == 'POST':
        print('About to close', task_id)
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise Http404("Task does not exist")

        decoded = jwt.decode(request.COOKIES['jwt'], settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
        my_id = decoded['id']
        if my_id != task.assignee.id:
            return HttpResponseServerError('You cannot close task not assigned to you')

        task.status = TaskStatus.CLOSED
        task.save()
        send_event(producer, 'tasks', registry, 1, TaskClosedBE(task_id=task.id, assignee_id=task.assignee.id))
        return HttpResponseRedirect(reverse('pjira:index'))

    return HttpResponseServerError("Wrong method")


@authorized_only(model=Employee, allowed_roles=[Role.MANAGER])
def assign_tasks(request):
    if request.method == 'POST':
        print('Assigning tasks')
        employee_list = Employee.objects.all()
        open_tasks = Task.objects.filter(status=TaskStatus.OPEN)
        for task in open_tasks:
            task.assignee = random.choice(employee_list)
            task.save()
            send_event(producer, 'tasks', registry, 1, TaskAssignedBE(task_id=task.id, assignee_id=task.assignee.id))
        return HttpResponseRedirect(reverse('pjira:index'))
    else:
        return render(request, 'pjira/assign_tasks.html')


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def employee_tasks(request, employee_id):
    try:
        me = Employee.objects.get(pk=employee_id)
    except Task.DoesNotExist:
        raise Http404("Employee {} does not exist".format(employee_id))
    open_tasks = Task.objects.filter(status=TaskStatus.OPEN, assignee=me).order_by('-open_date')
    return render(request, 'pjira/employee_tasks.html', {'open_tasks': open_tasks, 'me': me})
