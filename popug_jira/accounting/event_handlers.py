import random

from django.db import transaction

from .models import Task, Employee, Transaction, TransactionKind


def AccountCreatedHandler(event):
    emp = Employee.objects.create(id=event.account_id,
                                        name=event.name,
                                        roles=event.roles)
    emp.save()


def AccountChangedHandler(event):

    emp = Employee.objects.get(id=event.account_id)
    emp.name = event.name
    emp.roles = event.roles
    emp.save()


def TaskCreatedHandler(event):
    cost_assign = random.randint(10, 20)
    cost_close = random.randint(20, 40)
    emp = Task.objects.create(id=event.task_id,
                              description=event.description,
                              cost_assign=cost_assign,
                              cost_close=cost_close)
    emp.save()


def TaskAssignedHandler(event):

    with transaction.atomic():
        emp = Employee.objects.get(id=event.assignee_id)
        task = Task.objects.get(id=event.task_id)

        tr = Transaction.objects.create(account_id=emp,
                                        minus=task.cost_assign,
                                        description='Assign of task ' + task.description,
                                        kind=TransactionKind.TASK_ASSIGNED)
        tr.save()

        emp.wallet -= tr.minus
        emp.save()


def TaskClosedHandler(event):

    with transaction.atomic():
        emp = Employee.objects.get(id=event.assignee_id)
        task = Task.objects.get(id=event.task_id)

        tr = Transaction.objects.create(account_id=emp,
                                        plus=task.cost_close,
                                        description='Close of task ' + task.description,
                                        kind=TransactionKind.TASK_CLOSED)
        tr.save()

        emp.wallet += tr.plus
        emp.save()
