from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.urls import reverse
from django.conf import settings

from .forms import LoginForm, RegisterForm, ChangeAccountForm
from .models import Employee, Role

from common.authorized_only import authorized_only
from common.event_utils import send_event
from common.events.cud import AccountCreatedCUD, AccountChangedCUD, AccountCreatedCUDv2, AccountChangedCUDv2
from common.schema_registry import SchemaRegistry

import jwt
import json
import threading
from kafka import KafkaProducer, KafkaConsumer


registry = SchemaRegistry()
registry.register(1, AccountCreatedCUD)
registry.register(1, AccountChangedCUD)

registry.register(2, AccountCreatedCUDv2)
registry.register(2, AccountChangedCUDv2)


auth_service_producer = KafkaProducer(client_id='auth_service_accounts',
                                      bootstrap_servers=[settings.KAFKA_HOST],
                                      value_serializer=lambda m: json.dumps(m).encode('ascii'))


def update_employee_by_email(email, name, password, roles, phone_number, slack_id):
    try:
        acc = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        raise Http404("Account does not exist")

    acc.name = name
    acc.password = password
    acc.roles = roles
    acc.phone_number = phone_number
    acc.slack_id = slack_id
    acc.save()

    event = AccountChangedCUD(account_id=acc.id, name=acc.name, email=acc.email, roles=acc.roles)
    send_event(auth_service_producer, 'accounts', registry, 1, event)
    eventV2 = AccountChangedCUDv2(account_id=acc.id,
                                  name=acc.name,
                                  email=acc.email,
                                  roles=acc.roles,
                                  phone_number=acc.phone_number,
                                  slack_id=acc.slack_id)
    send_event(auth_service_producer, 'accounts', registry, 2, eventV2)

def create_employee(name, email, password, roles, phone_number, slack_id):
    emp_list = Employee.objects.filter(email=email)
    if len(emp_list) != 0:
        raise ValueError('Email already registered')

    emp = Employee.objects.create(name=name,
                                  email=email,
                                  password=password,
                                  roles=roles,
                                  phone_number=phone_number,
                                  slack_id=slack_id)
    emp.save()

    event = AccountCreatedCUD(account_id=emp.id, name=emp.name, email=emp.email, roles=emp.roles)
    send_event(auth_service_producer, 'accounts', registry, 1, event)
    eventV2 = AccountCreatedCUDv2(account_id=emp.id,
                                  name=emp.name,
                                  email=emp.email,
                                  roles=emp.roles,
                                  phone_number=emp.phone_number,
                                  slack_id=emp.slack_id)
    send_event(auth_service_producer, 'accounts', registry, 2, eventV2)


def login(request):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            resp = HttpResponseRedirect(reverse('pjira:index'))
            print(form.cleaned_data)
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                emp = Employee.objects.get(email=email)

                if emp.password != password:
                    raise ValueError('Password incorrect')

                encoded_jwt = jwt.encode({'id': emp.id, 'email': emp.email, 'roles': emp.roles}, settings.SECRET_KEY, algorithm=settings.JWT_ALGO)
                resp.set_cookie('jwt', encoded_jwt)
            except Exception as e:
                error_message = str(e)
                form = LoginForm()
                return render(request, 'auth_service/login.html', {'form': form, 'error_message': error_message})

            return resp
    else:
        form = LoginForm()

    return render(request, 'auth_service/login.html', {'form': form, 'error_message': error_message})


def register(request):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print(form.cleaned_data)
            try:

                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                repeat_password = form.cleaned_data['repeat_password']
                roles = [int(role) for role in form.cleaned_data['roles']]
                phone_number = form.cleaned_data['phone_number']
                slack_id = form.cleaned_data['slack_id']

                if password != repeat_password:
                    raise ValueError('Passwords do not match')

                create_employee(name, email, password, roles, phone_number, slack_id)

            except Exception as e:
                error_message = str(e)
                form = RegisterForm()
                return render(request, 'auth_service/register.html', {'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('auth_service:login'))
    else:
        form = RegisterForm()

    return render(request, 'auth_service/register.html', {'form': form, 'error_message': error_message})


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN])
def admin_list(request):
    accounts = Employee.objects.all().order_by('name')
    return render(request, 'auth_service/admin.html', {'accounts': accounts})


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN])
def change_account(request, account_id):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'GET':
        try:
            acc = Employee.objects.get(id=account_id)
        except Employee.DoesNotExist:
            raise Http404("Account does not exist")
        form = ChangeAccountForm(initial={'name':acc.name,
                                          'email':acc.email,
                                          'password':acc.password,
                                          'roles':acc.roles,
                                          'phone_number':acc.phone_number,
                                          'slack_id': acc.slack_id})
        return render(request, 'auth_service/change_account.html', {'form': form, 'error_message': error_message})

    raise HttpResponseServerError("Wrong method")


@authorized_only(model=Employee, allowed_roles=[Role.ADMIN])
def save_account_changes(request):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ChangeAccountForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print(form.cleaned_data)
            try:
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                roles = [int(role) for role in form.cleaned_data['roles']]
                phone_number = form.cleaned_data['phone_number']
                slack_id = form.cleaned_data['slack_id']

                update_employee_by_email(email, name, password, roles, phone_number, slack_id)

                return HttpResponseRedirect(reverse('auth_service:admin_list'))
                
            except Exception as e:
                error_message = str(e)
                form = ChangeAccountForm()
                return render(request, 'auth_service/change_account.html', {'form': form, 'error_message': error_message})

        else:
            return HttpResponseServerError("Form invalid: {}, errors: {}".format(form.cleaned_data, form.errors))
    else:
        return HttpResponseServerError("Wrong method")
