from .models import Employee, Task


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

def TaskAssignedHandler(event):
    emp = Employee.objects.get(id=event.assignee_id)
    task = Task.objects.get(id=event.task_id)
    text = 'Task `{}` was assigned to you'.format(task.description)
    if emp.email:
        print('[NOTIFICATION: email] To: {}, text: "{}"'.format(emp.email, text))
    if emp.phone_number:
        print('[NOTIFICATION: sms] To: {}, text: "{}"'.format(emp.phone_number, text))
    if emp.slack_id:
        print('[NOTIFICATION: slack] To: {}, text: "{}"'.format(emp.slack_id, text))
