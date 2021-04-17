from .models import Employee, Task
import logging

logger = logging.getLogger('root')


def AccountCreatedHandlerV2(event):
    emp = Employee.objects.create(public_id=event.account_public_id,
                                        name=event.name,
                                        email=event.email,
                                        phone_number=event.phone_number,
                                        slack_id=event.slack_id,
                                        roles=event.roles)
    emp.save()


def AccountChangedHandlerV2(event):

    emp = Employee.objects.get(public_id=event.account_public_id)
    emp.name = event.name
    emp.email = event.email
    emp.phone_number = event.phone_number
    emp.slack_id = event.slack_id
    emp.roles = event.roles
    emp.save()

def TaskAssignedHandler(event):
    emp = Employee.objects.get(public_id=event.assignee_public_id)
    task = Task.objects.get(public_id=event.task_public_id)
    text = 'Task `{}` was assigned to you'.format(task.description)
    if emp.email:
        logger.info('[NOTIFICATION: email] To: {}, text: "{}"'.format(emp.email, text))
    if emp.phone_number:
        logger.info('[NOTIFICATION: sms] To: {}, text: "{}"'.format(emp.phone_number, text))
    if emp.slack_id:
        logger.info('[NOTIFICATION: slack] To: {}, text: "{}"'.format(emp.slack_id, text))
