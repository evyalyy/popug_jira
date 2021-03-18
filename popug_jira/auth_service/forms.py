from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(label='email', max_length=200)
    password = forms.CharField(label='password', max_length=200)


class RegisterForm(forms.Form):
    name = forms.CharField(label='name', max_length=200)
    email = forms.EmailField(label='email', max_length=200)
    password = forms.CharField(label='password', max_length=200)
    repeat_password = forms.CharField(label='repeat_password', max_length=200)
