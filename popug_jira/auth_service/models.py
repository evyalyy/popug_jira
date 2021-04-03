from django.db import models

from django.core.validators import RegexValidator

phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

class Role(models.IntegerChoices):
    EMPLOYEE = 1
    ADMIN = 2
    BUH = 3
    MANAGER = 4

class Employee(models.Model):
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    slack_id = models.CharField(max_length=200, blank=True, null=True)
    roles = models.JSONField(default=list)

    def __str__(self):
        return 'Name: {}, email: {}, roles: {}'.format(self.name, self.email, ','.join([Role(r).label for r in self.roles]))
