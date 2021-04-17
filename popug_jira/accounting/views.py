from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.conf import settings
from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind

from auth_service.models import Role

from common.authorized_only import authorized_only
from common.event_utils import send_event, consume_events
from common.events.business import TaskCreated, TaskAssigned, TaskClosed, DailyPaymentCompleted
from common.events.cud import AccountCreatedv2, AccountChangedv2, TransactionCreated, TaskCostAssigned
from common.schema_registry import SchemaRegistry
from .event_handlers import *

import random
import requests
import jwt
import threading
from datetime import datetime
import time
import logging
from kafka import KafkaProducer, KafkaConsumer

logger = logging.getLogger('root')


producer_transactions = KafkaProducer(client_id='accounting_transactions',
                         bootstrap_servers=[settings.KAFKA_HOST],
                         value_serializer=lambda m: m.encode('ascii'))

producer_tasks = KafkaProducer(client_id='accounting_tasks',
                         bootstrap_servers=[settings.KAFKA_HOST],
                         value_serializer=lambda m: m.encode('ascii'))

registry = SchemaRegistry()
registry.register(2, AccountCreatedv2, AccountCreatedHandlerV2)
registry.register(2, AccountChangedv2, AccountChangedHandlerV2)

registry.register(1, TaskCreated, lambda event: TaskCreatedHandler(event, producer_tasks, 'tasks', registry, 1))
registry.register(1, TaskAssigned, lambda event: TaskAssignedHandler(event, producer_transactions, 'transactions', registry, 1))
registry.register(1, TaskClosed, lambda event: TaskClosedHandler(event, producer_transactions, 'transactions', registry, 1))
registry.register(1, DailyPaymentCompleted, DailyPaymentCompletedHandler)
registry.register(1, TaskCostAssigned)
registry.register(1, TransactionCreated)


accounts_consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
tasks_consumer = KafkaConsumer('tasks', bootstrap_servers=[settings.KAFKA_HOST])
transactions_consumer = KafkaConsumer('transactions', bootstrap_servers=[settings.KAFKA_HOST])


def run_at_end_of_day():
    last_eod_time = datetime.now()
    while True:
        now = datetime.now()
        if now.minute != last_eod_time.minute: # FIXME: payoff every minute, not day
            logger.info('END OF DAY')
            employees = Employee.objects.all()
            for emp in employees:
                if emp.wallet > 0:
                    with transaction.atomic():
                        logger.info('payoff for employee {}, amount: {}'.format(emp, emp.wallet))
                        tr = Transaction.objects.create(account_id=emp,
                                            minus=emp.wallet,
                                            description='Payoff for ' + str(now),
                                            kind=TransactionKind.DAILY_PAYMENT)
                        tr.save()

                        emp.wallet = 0
                        emp.save()

                        send_event(producer_transactions, 'transactions', registry, 1, DailyPaymentCompleted(account_public_id=emp.public_id,
                                                                                                             amount=tr.minus,
                                                                                                             ts=datetime.now()))

        last_eod_time = now
        time.sleep(10)


thr = threading.Thread(target=consume_events, args=(accounts_consumer, registry, 'accounting'))
thr.start()
thr2 = threading.Thread(target=consume_events, args=(tasks_consumer, registry, 'accounting'))
thr2.start()
thr3 = threading.Thread(target=run_at_end_of_day)
thr3.start()
thr4 = threading.Thread(target=consume_events, args=(transactions_consumer, registry, 'accounting'))
thr4.start()


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def index(request):
    employees = Employee.objects.all()
    now = datetime.now()

    transactions = Transaction.objects.filter(ts__year=now.year,
                                              ts__month=now.month,
                                              ts__day=now.day).exclude(kind=TransactionKind.DAILY_PAYMENT)

    total = 0
    for tr in transactions:
        total += tr.plus - tr.minus
    total *= -1

    return render(request, 'accounting/index.html', {'employees': employees, 'total': total})


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN, Role.BUH])
def employee_details(request, employee_id):
    try:
        me = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        raise Http404("Employee {} does not exist".format(employee_id))
    now = datetime.now()
    transactions = Transaction.objects.filter(account_id=me.id, ts__year=now.year, ts__month=now.month, ts__day=now.day).order_by('-ts')
    return render(request, 'accounting/employee_details.html', {'transactions': transactions, 'me': me})
