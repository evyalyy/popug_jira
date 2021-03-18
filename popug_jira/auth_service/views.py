from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.urls import reverse
from django.conf import settings

from .forms import LoginForm, RegisterForm, ChangeAccountForm
from .models import Employee, Role

from common.authorized_only import authorized_only

import jwt

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

                encoded_jwt = jwt.encode({'email': emp.email, 'roles': emp.role}, settings.SECRET_KEY, algorithm=settings.JWT_ALGO)
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

                emp_list = Employee.objects.filter(email=email)
                if len(emp_list) != 0:
                    raise ValueError('Email already registered')

                emp = Employee.objects.create(name=name, email=email, password=password, role=[Role.EMPLOYEE])
                emp.save()
            except Exception as e:
                error_message = str(e)
                form = RegisterForm()
                return render(request, 'auth_service/register.html', {'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('pjira:index'))
    else:
        form = RegisterForm()

    return render(request, 'auth_service/register.html', {'form': form, 'error_message': error_message})

@authorized_only(roles=[Role.ADMIN])
def admin_list(request):
    accounts = Employee.objects.all().order_by('name')
    return render(request, 'auth_service/admin.html', {'accounts': accounts})


@authorized_only(roles=[Role.ADMIN])
def change_account(request, account_id):
    # if this is a POST request we need to process the form data
    error_message = None
    if request.method == 'GET':
        try:
            acc = Employee.objects.get(id=account_id)
        except Employee.DoesNotExist:
            raise Http404("Account does not exist")
        form = ChangeAccountForm(initial={'name':acc.name, 'email':acc.email, 'password':acc.password, 'roles':acc.role})
        return render(request, 'auth_service/change_account.html', {'form': form, 'error_message': error_message})

    raise HttpResponseServerError("Wrong method")


@authorized_only(roles=[Role.ADMIN])
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
                print(roles)
                try:
                    acc = Employee.objects.get(email=email)
                except Employee.DoesNotExist:
                    raise Http404("Account does not exist")
                acc.name = name
                acc.email = email
                acc.password = password
                acc.role = roles
                acc.save()
            except Exception as e:
                error_message = str(e)
                form = ChangeAccountForm()
                return render(request, 'auth_service/change_account.html', {'form': form, 'error_message': error_message})

            return HttpResponseRedirect(reverse('auth_service:admin_list'))
    else:
        raise HttpResponseServerError("Wrong method")
