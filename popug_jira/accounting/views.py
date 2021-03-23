from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind
from auth_service.models import Role

from common.authorized_only import authorized_only
from common.events import send_event, get_schema_by_name
from common.events import AccountCreatedCUDSchema, AccountChangedCUDSchema, AccountRoleChangedCUDSchema
from common.events import TaskCreatedBE, TaskAssignedBE, TaskClosedBE

import random
import requests
import jwt
import json
import threading
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer


producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_HOST], value_serializer=lambda m: json.dumps(m).encode('ascii'))

accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])

stop_consumers = False


def consume_accounts(js):
    meta = js['meta']
    if meta['version'] != 1:
        print('[ACCOUNTING][ERROR] wrong version. meta:', meta)
        return

    sch = get_schema_by_name(1, meta['event_type'])

    errors = sch().validate(js)
    
    if len(errors) > 0:
        print('[ACCOUNTING][ERROR] consume validation errors: {}'.format(errors))
        return

    if sch == AccountCreatedCUDSchema:
        emp = Employee.objects.create(id=js['account_id'], name=js['name'], roles=js['roles'])
        emp.save()
    elif sch == AccountChangedCUDSchema:
        try:
            emp = Employee.objects.get(id=js['account_id'])
            emp.name = js['name']
            emp.save()
        except Employee.DoesNotExist:
            print('[ACCOUNTING][ERROR] account does not exist')
    elif sch == AccountRoleChangedCUDSchema:
        try:
            emp = Employee.objects.get(id=js['account_id'])
            emp.roles = js['roles']
            emp.save()
        except Employee.DoesNotExist:
            print('[ACCOUNTING][ERROR] account does not exist')


def consume_tasks(js):
    tp = js['type']

    if tp == TaskCreatedBE.__name__:
        cost_assign = random.randint(10, 20)
        cost_close = random.randint(20, 40)
        emp = Task.objects.create(id=js['id'], description=js['description'], cost_assign=cost_assign, cost_close=cost_close)
        emp.save()
    elif tp == TaskAssignedBE.__name__:
        try:
            with transaction.atomic():
                emp = Employee.objects.get(id=js['assignee'])
                task = Task.objects.get(id=js['id'])

                tr = Transaction.objects.create(account_id=emp,
                                                minus=task.cost_assign,
                                                description='Assign of task ' + task.description,
                                                kind=TransactionKind.TASK_ASSIGNED)
                tr.save()

                emp.wallet -= tr.minus
                emp.save()
        except Employee.DoesNotExist:
            print('[ACCOUNTING][ERROR] account does not exist')
        except Task.DoesNotExist:
            print('[ACCOUNTING][ERROR] task does not exist')
        except Exception as e:
            print('[ACCOUNTING][ERROR]', e)
    elif tp == TaskClosedBE.__name__:
        try:
            with transaction.atomic():
                emp = Employee.objects.get(id=js['assignee'])
                task = Task.objects.get(id=js['id'])

                tr = Transaction.objects.create(account_id=emp,
                                                plus=task.cost_close,
                                                description='Close of task ' + task.description,
                                                kind=TransactionKind.TASK_CLOSED)
                tr.save()

                emp.wallet += tr.plus
                emp.save()
        except Employee.DoesNotExist:
            print('[ACCOUNTING][ERROR] account does not exist')
        except Task.DoesNotExist:
            print('[ACCOUNTING][ERROR] task does not exist')
        except Exception as e:
            print('[ACCOUNTING][ERROR]', e)


def consumer_func(consumer, func):
    global stop_consumers
    print('[ACCOUNTING] CONSUMERS STARTED')
    while not stop_consumers:
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print ("[ACCOUNTING] consumed %s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                  message.offset, message.key,
                                                  message.value))
            js = json.loads(message.value.decode('ascii'))
            print('[ACCOUNTING] type:', js['meta'])

            func(js)


thr = threading.Thread(target=consumer_func, args=(accounts_consumer, consume_accounts))
thr.start()
thr2 = threading.Thread(target=consumer_func, args=(tasks_consumer, consume_tasks))
thr2.start()


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def index(request):
    employees = Employee.objects.all()
    now = datetime.now()
    transactions = Transaction.objects.filter(ts__year=now.year, ts__month=now.month, ts__day=now.day)
    total = 0
    for tr in transactions:
        total += tr.plus - tr.minus
    print('Total:', total)
    print(employees)
    return render(request, 'accounting/index.html', {'employees': employees, 'total': total})


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def employee_details(request, employee_id):
    try:
        me = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        raise Http404("Employee {} does not exist".format(employee_id))
    print('ME',me)
    now = datetime.now()
    print(now)
    transactions = Transaction.objects.filter(account_id=me.id, ts__year=now.year, ts__month=now.month, ts__day=now.day).order_by('-ts')
    print('My transactions', transactions)
    return render(request, 'accounting/employee_details.html', {'transactions': transactions, 'me': me})
