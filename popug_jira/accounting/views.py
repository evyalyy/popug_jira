from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind
from auth_service.models import Role

from common.authorized_only import authorized_only
from common.events import send_event, consume_accounts, consumer_func, get_schema_type_from_meta
from common.events import TaskCreatedBESchema, TaskAssignedBESchema, TaskClosedBESchema

import random
import requests
import jwt
import json
import threading
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer


producer = KafkaProducer(client_id='accounting_transactions',
                         bootstrap_servers=[settings.KAFKA_HOST],
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))

accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])


def consume_tasks(message_json, label):
    
    schema_type = get_schema_type_from_meta(message_json, 1)
    if schema_type is None:
        # Need some handling of unexpected version
        print('Incompatible version')
        return

    errors = schema_type().validate(message_json)
    
    if len(errors) > 0:
        print('[{}][ERROR] consume validation errors: {}'.format(label, errors))
        return

    if schema_type == TaskCreatedBESchema:
        cost_assign = random.randint(10, 20)
        cost_close = random.randint(20, 40)
        emp = Task.objects.create(id=message_json['task_id'],
                                  description=message_json['description'],
                                  cost_assign=cost_assign,
                                  cost_close=cost_close)
        emp.save()
    elif schema_type == TaskAssignedBESchema:
        try:
            with transaction.atomic():
                emp = Employee.objects.get(id=message_json['assignee_id'])
                task = Task.objects.get(id=message_json['task_id'])

                tr = Transaction.objects.create(account_id=emp,
                                                minus=task.cost_assign,
                                                description='Assign of task ' + task.description,
                                                kind=TransactionKind.TASK_ASSIGNED)
                tr.save()

                emp.wallet -= tr.minus
                emp.save()
        except Employee.DoesNotExist:
            print('[{}][ERROR] account does not exist'.format(label))
        except Task.DoesNotExist:
            print('[{}][ERROR] task does not exist'.format(label))
        except Exception as e:
            print('[{}][ERROR] {}'.format(label,e))
    elif schema_type == TaskClosedBESchema:
        try:
            with transaction.atomic():
                emp = Employee.objects.get(id=message_json['assignee_id'])
                task = Task.objects.get(id=message_json['task_id'])

                tr = Transaction.objects.create(account_id=emp,
                                                plus=task.cost_close,
                                                description='Close of task ' + task.description,
                                                kind=TransactionKind.TASK_CLOSED)
                tr.save()

                emp.wallet += tr.plus
                emp.save()
        except Employee.DoesNotExist:
            print('[{}][ERROR] account does not exist'.format(label))
        except Task.DoesNotExist:
            print('[{}][ERROR] task does not exist'.format(label))
        except Exception as e:
            print('[{}][ERROR] {}'.format(label,e))


thr = threading.Thread(target=consumer_func, args=(accounts_consumer, consume_accounts, 'accounting', Employee))
thr.start()
thr2 = threading.Thread(target=consumer_func, args=(tasks_consumer, consume_tasks, 'accounting'))
thr2.start()


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def index(request):
    employees = Employee.objects.all()
    now = datetime.now()
    transactions = Transaction.objects.filter(ts__year=now.year, ts__month=now.month, ts__day=now.day)
    total = 0
    for tr in transactions:
        total += tr.plus - tr.minus
    return render(request, 'accounting/index.html', {'employees': employees, 'total': total})


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def employee_details(request, employee_id):
    try:
        me = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        raise Http404("Employee {} does not exist".format(employee_id))
    now = datetime.now()
    print(now)
    transactions = Transaction.objects.filter(account_id=me.id, ts__year=now.year, ts__month=now.month, ts__day=now.day).order_by('-ts')
    return render(request, 'accounting/employee_details.html', {'transactions': transactions, 'me': me})
