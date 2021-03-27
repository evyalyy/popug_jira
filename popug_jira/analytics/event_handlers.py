from .models import Task, Employee, TaskFact
from accounting.models import TransactionKind

from django.utils.timezone import make_aware

def AccountCreatedHandlerV2(event):
    emp = Employee.objects.create(id=event.account_id,
                                  name=event.name,
                                  roles=event.roles)
    emp.save()


def AccountChangedHandlerV2(event):

    emp = Employee.objects.get(id=event.account_id)
    emp.name = event.name
    emp.roles = event.roles
    emp.save()


def TaskCostAssignedHandler(event):
    task = Task.objects.create(id=event.task_id,
                               description=event.description,
                               cost_assign=event.cost_assign,
                               cost_close=event.cost_close)

    task.save()


def TransactionCreatedHandler(event):
    emp = Employee.objects.get(id=event.account_id)
    task = Task.objects.get(id=event.task_id)
    fact = TaskFact.objects.create(fact_ts=make_aware(event.ts),
                                   kind=event.kind,
                                   assignee=emp,
                                   task_id=task.id)

    fact.save()
