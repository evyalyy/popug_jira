import random
from datetime import datetime

from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind

from common.events.cud import TaskCostAssigned, TransactionCreated
from common.event_utils import send_event
import logging

logger = logging.getLogger('root')

def AccountCreatedHandlerV2(event):
    emp = Employee.objects.create(public_id=event.account_public_id,
                                        name=event.name,
                                        email=event.email,
                                        roles=event.roles)
    emp.save()


def AccountChangedHandlerV2(event):

    emp = Employee.objects.get(public_id=event.account_public_id)
    emp.name = event.name
    emp.email = event.email
    emp.roles = event.roles
    emp.save()


def TaskCreatedHandler(event, producer, topic, schema_registry, version):
    cost_assign = random.randint(10, 20)
    cost_close = random.randint(20, 40)
    with transaction.atomic():
        task = Task.objects.create(public_id=event.task_public_id,
                                  description=event.description,
                                  cost_assign=cost_assign,
                                  cost_close=cost_close)
        task.save()

        send_event(producer, topic, schema_registry, version, TaskCostAssigned(task_public_id=str(task.public_id),
                                                                               description=task.description,
                                                                               cost_assign=cost_assign,
                                                                               cost_close=cost_close))


def TaskAssignedHandler(event, producer, topic, schema_registry, version):

    with transaction.atomic():
        emp = Employee.objects.get(public_id=event.assignee_public_id)
        task = Task.objects.get(public_id=event.task_public_id)

        tr = Transaction.objects.create(account_id=emp,
                                        minus=task.cost_assign,
                                        description='Assign of task ' + task.description,
                                        kind=TransactionKind.TASK_ASSIGNED)
        tr.save()

        emp.wallet -= tr.minus
        emp.save()

        send_event(producer, topic, schema_registry, version, TransactionCreated(account_public_id=str(emp.public_id),
                                                                                 task_public_id=str(task.public_id),
                                                                                 kind=TransactionKind.TASK_ASSIGNED,
                                                                                 ts = datetime.now()))


def TaskClosedHandler(event, producer, topic, schema_registry, version):

    with transaction.atomic():
        emp = Employee.objects.get(public_id=event.assignee_public_id)
        task = Task.objects.get(public_id=event.task_public_id)

        tr = Transaction.objects.create(account_id=emp,
                                        plus=task.cost_close,
                                        description='Close of task ' + task.description,
                                        kind=TransactionKind.TASK_CLOSED)
        tr.save()

        emp.wallet += tr.plus
        emp.save()

        send_event(producer, topic, schema_registry, version, TransactionCreated(account_public_id=str(emp.public_id),
                                                                                 task_public_id=str(task.public_id),
                                                                                 kind=TransactionKind.TASK_CLOSED,
                                                                                 ts = datetime.now()))


def DailyPaymentCompletedHandler(event):
      emp = Employee.objects.get(public_id=event.account_public_id)
      text = 'Hello, {}, UberPopug inc. sent you money for today: {}'.format(emp.name, event.amount)
      if emp.email:
          logger.info('[NOTIFICATION: email] To: {}, text: "{}"'.format(emp.email, text))
