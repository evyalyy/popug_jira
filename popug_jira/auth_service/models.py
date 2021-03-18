from django.db import models

class Role(models.IntegerChoices):
    EMPLOYEE = 1
    ADMIN = 2
    BUH = 3
    MANAGER = 4

class Employee(models.Model):
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.EmailField()
    role = models.JSONField(default=list)

    def __str__(self):
        return self.name
