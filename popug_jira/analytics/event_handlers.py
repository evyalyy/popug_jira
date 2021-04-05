from .models import Task, Employee, TaskFact
from accounting.models import TransactionKind

from django.utils.timezone import make_aware

def AccountCreatedHandlerV2(event):
    emp = Employee.objects.create(public_id=event.account_public_id,
                                  name=event.name,
                                  roles=event.roles)
    emp.save()


def AccountChangedHandlerV2(event):

    emp = Employee.objects.get(public_id=event.account_public_id)
    emp.name = event.name
    emp.roles = event.roles
    emp.save()


def TaskCostAssignedHandler(event):
    task = Task.objects.create(public_id=event.task_public_id,
                               description=event.description,
                               cost_assign=event.cost_assign,
                               cost_close=event.cost_close)

    task.save()


def TransactionCreatedHandler(event):
    emp = Employee.objects.get(public_id=event.account_public_id)
    task = Task.objects.get(public_id=event.task_public_id)
    fact = TaskFact.objects.create(fact_ts=make_aware(event.ts),
                                   kind=event.kind,
                                   assignee=emp,
                                   task_id=task.id)

    fact.save()
