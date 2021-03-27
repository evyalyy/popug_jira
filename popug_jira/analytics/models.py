from django.db import models

from accounting.models import TransactionKind


class Employee(models.Model):
    name = models.CharField(max_length=200)
    roles = models.JSONField(default=list)


class Task(models.Model):
    description = models.CharField(max_length=4096)
    cost_assign = models.IntegerField(default=0)
    cost_close = models.IntegerField(default=0)


class TaskFact(models.Model):
    fact_ts = models.DateTimeField()
    kind = models.IntegerField(choices=TransactionKind.choices)
    assignee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return 'TaskFact(ts={},kind={},assignee={},task={})'.format(self.fact_ts, TransactionKind(self.kind).label, self.assignee, self.task)

    def __repr__(self):
        return self.__str__()
