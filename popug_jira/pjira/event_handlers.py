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

def AccountCreatedHandlerV2(event):
    emp = Employee.objects.create(id=event.account_id,
                                        name=event.name,
                                        email=event.email,
                                        phone_number=event.phone_number,
                                        slack_id=event.slack_id,
                                        roles=event.roles)
    emp.save()


def AccountChangedHandlerV2(event):

    emp = Employee.objects.get(id=event.account_id)
    emp.name = event.name
    emp.email = event.email
    emp.phone_number = event.phone_number
    emp.slack_id = event.slack_id
    emp.roles = event.roles
    emp.save()
