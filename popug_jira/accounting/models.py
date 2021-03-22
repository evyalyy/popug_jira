from django.db import models

from auth_service.models import Role

class Employee(models.Model):
    name = models.CharField(max_length=200)
    roles = models.JSONField(default=list)
    wallet = models.IntegerField(default=0)

    def __str__(self):
        return '{}, roles: {}'.format(self.name, ','.join([Role(r).label for r in self.roles]))

class Task(models.Model):
    description = models.CharField(max_length=4096)
    cost_assign = models.IntegerField(default=0)
    cost_close = models.IntegerField(default=0)

class TransactionKind(models.IntegerChoices):
    TASK_CLOSED = 1
    TASK_ASSIGNED = 2
    DAILY_PAYMENT = 3

class Transaction(models.Model):
    account_id = models.ForeignKey(Employee, on_delete=models.CASCADE)
    ts = models.DateTimeField(auto_now=True)
    plus = models.IntegerField(default=0)
    minus = models.IntegerField(default=0)
    description = models.CharField(max_length=4096)
    kind = models.IntegerField(choices=TransactionKind.choices)
