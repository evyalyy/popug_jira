from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
from django.db import transaction

from .models import Task, Employee, TaskStatus
from .forms import AddTaskForm
from auth_service.models import Role

from common.authorized_only import authorized_only
from common.event_utils import send_event, consume_events
from common.events.business import TaskCreated, TaskAssigned, TaskClosed
from common.events.cud import AccountCreatedv2, AccountChangedv2
from common.schema_registry import SchemaRegistry
from .event_handlers import *

import random
import requests
import jwt
import threading
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer


registry = SchemaRegistry()
registry.register(2, AccountCreatedv2, AccountCreatedHandlerV2)
registry.register(2, AccountChangedv2, AccountChangedHandlerV2)

registry.register(1, TaskCreated)
registry.register(1, TaskAssigned, TaskAssignedHandler)
registry.register(1, TaskClosed)


producer = KafkaProducer(client_id='pjira_tasks',
                        bootstrap_servers=[settings.KAFKA_HOST],
                        value_serializer=lambda m: m.encode('ascii'))

accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])


thr1 = threading.Thread(target=consume_events, args=(accounts_consumer, registry, 'pjira'))
thr1.start()
thr2 = threading.Thread(target=consume_events, args=(tasks_consumer, registry, 'pjira'))
thr2.start()

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
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddTaskForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            try:
                with transaction.atomic():
                    new_task = Task.objects.create(description=form.cleaned_data['description'])
                    new_task.save()
                    send_event(producer, 'tasks', registry, 1, TaskCreated(task_public_id=str(new_task.public_id), description=new_task.description))
            except Exception as e:
                error_message = str(e)
                return render(request, 'pjira/add_task.html', {'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('pjira:index'))
    else:
        form = AddTaskForm()

    return render(request, 'pjira/add_task.html', {'form': form})


@authorized_only(model=Employee, allowed_roles=[Role.EMPLOYEE])
def close_task(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise Http404("Task does not exist")

        if task.assignee is None:
            return HttpResponseServerError('Cannot close not assigned task')

        decoded = jwt.decode(request.COOKIES['jwt'], settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])
        my_id = decoded['id']
        if my_id != str(task.assignee.public_id):
            return HttpResponseServerError('You cannot close task not assigned to you')

        with transaction.atomic():
            task.status = TaskStatus.CLOSED
            task.save()
            send_event(producer, 'tasks', registry, 1, TaskClosed(task_public_id=str(task.public_id), assignee_public_id=str(task.assignee.public_id)))
        return HttpResponseRedirect(reverse('pjira:index'))

    return HttpResponseServerError("Wrong method")


@authorized_only(model=Employee, allowed_roles=[Role.MANAGER])
def assign_tasks(request):
    if request.method == 'POST':
        employee_list = Employee.objects.all()
        open_tasks = Task.objects.filter(status=TaskStatus.OPEN)
        with transaction.atomic():
            for task in open_tasks:
                task.assignee = random.choice(employee_list)
                task.save()
                send_event(producer, 'tasks', registry, 1, TaskAssigned(task_public_id=str(task.public_id),
                                                                          assignee_public_id=str(task.assignee.public_id)))
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
