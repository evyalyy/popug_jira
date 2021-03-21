from django.db import models

from auth_service.models import Role

class TaskStatus(models.IntegerChoices):
    OPEN = 1, 'OPEN'
    CLOSED = 2, 'CLOSED'

class Employee(models.Model):
    name = models.CharField(max_length=200)
    roles = models.JSONField(default=list)

    def __str__(self):
        return '{}, roles: {}'.format(self.name, ','.join([Role(r).label for r in self.roles]))


class Task(models.Model):
    description = models.CharField(max_length=4096)
    status = models.IntegerField(choices=TaskStatus.choices, default=TaskStatus.OPEN)
    open_date = models.DateTimeField(auto_now=True)
    close_date = models.DateTimeField('date closed', blank=True, null=True)
    cost = models.IntegerField(default=0)
    assignee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return 'Task(desc={}, status={}, assignee={}, cost={}, opened={}, closed={})'.format(
            self.description,
            self.status,
            self.assignee if self.assignee else 'Not assigned',
            self.cost,
            self.open_date,
            self.close_date if self.close_date else 'Not yet closed')
