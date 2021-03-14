from django import forms

class AddTaskForm(forms.Form):
    description = forms.CharField(label='Description', max_length=4096)
    # assignee = forms.CharField(label='Assignee', max_length=200)
