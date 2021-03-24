from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
# from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind

from auth_service.models import Role

from common.authorized_only import authorized_only
from common.event_utils import send_event, consume_events
from common.events.business import TaskCreatedBE, TaskAssignedBE, TaskClosedBE
from common.events.cud import AccountCreatedCUD, AccountChangedCUD
from common.schema_registry import SchemaRegistry
from .event_handlers import *

import random
import requests
import jwt
import json
import threading
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer


registry = SchemaRegistry()
registry.register(1, AccountCreatedCUD, AccountCreatedHandler)
registry.register(1, AccountChangedCUD, AccountChangedHandler)
registry.register(1, TaskCreatedBE, TaskCreatedHandler)
registry.register(1, TaskAssignedBE, TaskAssignedHandler)
registry.register(1, TaskClosedBE, TaskClosedHandler)


producer = KafkaProducer(client_id='accounting_transactions',
                         bootstrap_servers=[settings.KAFKA_HOST],
                         value_serializer=lambda m: json.dumps(m).encode('ascii'))

accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])


thr = threading.Thread(target=consume_events, args=(accounts_consumer, registry, 'accounting'))
thr.start()
thr2 = threading.Thread(target=consume_events, args=(tasks_consumer, registry, 'accounting'))
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
