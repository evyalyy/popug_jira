from .models import Employee


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
