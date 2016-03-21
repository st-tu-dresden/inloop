from django import forms
from inloop.tasks.models import TaskCategory
import datetime


def get_task_categories():
    res = []
    for c in TaskCategory.objects.all():
        res.append(c.get_tuple())
    return res


YESNO_CHOICES = [('Y', 'Yes'),
                 ('N', 'No')]


def tomorrow():
    return datetime.datetime.now() + datetime.timedelta(1)


def datetime_now():
    return datetime.datetime.now()


class ExerciseSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(ExerciseSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['e_cat'] = forms.ChoiceField(
            choices=get_task_categories(),
            label='Exercise Category',
            widget=forms.Select(attrs={
                'class': 'form-control'
            }))

    # TODO: Add validators for file size, ending and header
    e_title = forms.CharField(
        max_length=100,
        label='Exercise Title',
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        }))
    e_desc = forms.CharField(
        label='Description',
        widget=forms.Textarea(attrs={
            'class': 'form-control no-resize'
        }))
    e_pub_date = forms.DateTimeField(
        initial=datetime_now,
        label='Publication Date',
        input_formats=['%m/%d/%Y %H:%M'],
        widget=forms.DateTimeInput(
            format='%m/%d/%Y %H:%M',
            attrs={
                'class': 'form-control'
            }
        ))
    e_dead_date = forms.DateTimeField(
        initial=tomorrow,
        label='Deadline Date',
        input_formats=['%m/%d/%Y %H:%M'],
        widget=forms.DateTimeInput(
            format='%m/%d/%Y %H:%M',
            attrs={
                'class': 'form-control'
            }
        ))
    ut_files = forms.FileField(
        label='Unittest Files',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'multiple': '1'
        }))
    e_files = forms.FileField(
        label='Exercise Templates',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'multiple': '1'
        }))
