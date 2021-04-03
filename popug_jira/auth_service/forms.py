from django import forms

from .models import Role, phone_regex

class LoginForm(forms.Form):
    email = forms.CharField(label='email', max_length=200)
    password = forms.CharField(label='password', max_length=200)


class RegisterForm(forms.Form):
    name = forms.CharField(label='name', max_length=200)
    email = forms.EmailField(label='email', max_length=200)
    password = forms.CharField(label='password', max_length=200)
    repeat_password = forms.CharField(label='repeat_password', max_length=200)
    phone_number = forms.CharField(validators=[phone_regex], max_length=20)
    slack_id = forms.CharField(max_length=200)
    roles = forms.MultipleChoiceField(choices=Role.choices)

class ChangeAccountForm(forms.Form):
    name = forms.CharField(label='name', max_length=200)
    email = forms.EmailField(label='email', max_length=200)
    password = forms.CharField(label='password', max_length=200)
    roles = forms.MultipleChoiceField(choices=Role.choices)
    phone_number = forms.CharField(validators=[phone_regex], max_length=20)
    slack_id = forms.CharField(max_length=200)
