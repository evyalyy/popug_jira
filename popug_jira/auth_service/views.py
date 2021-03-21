from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.urls import reverse
from django.conf import settings

from .forms import LoginForm, RegisterForm, ChangeAccountForm
from .models import Employee, Role

from common.authorized_only import authorized_only
from common.events import send_event, AccountCreatedCUD, AccountChangedCUD, AccountRoleChangedCUD

import jwt

import json
import threading
from kafka import KafkaProducer, KafkaConsumer

producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_HOST], value_serializer=lambda m: json.dumps(m).encode('ascii'))
# consumer = KafkaConsumer('accounts', bootstrap_servers=[settings.KAFKA_HOST])
# stop_consumers = False

# def consumer_func():
#     global stop_consumers
#     print('[AUTH] CONSUMERS STARTED')
#     while not stop_consumers:
#         for message in consumer:
#             # message value and key are raw bytes -- decode if necessary!
#             # e.g., for unicode: `message.value.decode('utf-8')`
#             print ("[AUTH] consumed %s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
#                                                   message.offset, message.key,
#                                                   message.value))
# thr = threading.Thread(target=consumer_func)
# thr.start()

def update_employee_by_email(email, name, password, roles):
    try:
        acc = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        raise Http404("Account does not exist")

    roles_changed_event = None
    if acc.roles != roles:
        roles_changed_event = AccountRoleChangedCUD(id=acc.id, roles=roles)

    acc.name = name
    acc.password = password
    acc.roles = roles
    acc.save()

    event = AccountChangedCUD(id=acc.id, name=acc.name, email=acc.email)
    send_event(producer, 'accounts', event)

    if roles_changed_event:
        send_event(producer, 'accounts', roles_changed_event)


def create_employee(name, email, password):
    emp_list = Employee.objects.filter(email=email)
    if len(emp_list) != 0:
        raise ValueError('Email already registered')

    emp = Employee.objects.create(name=name, email=email, password=password, roles=[Role.EMPLOYEE])
    emp.save()

    event = AccountCreatedCUD(id=emp.id, name=emp.name, email=emp.email)
    send_event(producer, 'accounts', event)


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

                if password != repeat_password:
                    raise ValueError('Passwords do not match')

                create_employee(name, email, password)

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
        form = ChangeAccountForm(initial={'name':acc.name, 'email':acc.email, 'password':acc.password, 'roles':acc.roles})
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

                update_employee_by_email(email, name, password, roles)

                return HttpResponseRedirect(reverse('auth_service:admin_list'))
                
            except Exception as e:
                error_message = str(e)
                form = ChangeAccountForm()
                return render(request, 'auth_service/change_account.html', {'form': form, 'error_message': error_message})

        else:
            return HttpResponseServerError("Form invalid: {}, errors: {}".format(form.cleaned_data, form.errors))
    else:
        return HttpResponseServerError("Wrong method")
