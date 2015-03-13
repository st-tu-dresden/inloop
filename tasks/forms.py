from django import forms
from tinymce.widgets import TinyMCE
from tasks.models import TASK_CATEGORIES
import datetime


def tomorrow():
    return datetime.datetime.now() + datetime.timedelta(1)


def datetime_now():
    return datetime.datetime.now()


class UserEditorForm(forms.Form):
    content = forms.CharField(
        label='',
        widget=TinyMCE(attrs={
            'cols': 100,
            'rows': 20
        }))


class ExerciseSubmissionForm(forms.Form):
    # TODO: Add validators for file size, ending and header
    e_title = forms.CharField(max_length=100,
                              label='Exercise Title',
                              widget=forms.TextInput(attrs={
                                  'class': 'form-control'
                              }))
    e_desc = forms.CharField(label='Description',
                             widget=TinyMCE(attrs={
                                 'cols': 100,
                                 'rows': 20,
                                 'class': 'form-control'
                             }))
    e_pub_date = forms.DateTimeField(initial=datetime_now,
                                     label='Publication Date',
                                     widget=forms.DateTimeInput(attrs={
                                         'class': 'form-control'
                                     }))
    e_dead_date = forms.DateTimeField(initial=tomorrow,
                                      label='Deadline Date',
                                      widget=forms.DateTimeInput(attrs={
                                          'class': 'form-control'
                                      }))
    e_cat = forms.ChoiceField(choices=TASK_CATEGORIES,
                              label='Exercise Category',
                              widget=forms.Select(attrs={
                                  'class': 'form-control'
                              }))
    ut_files = forms.FileField(label='Unittest Files',
                               widget=forms.FileInput(attrs={
                                   'class': 'form-control',
                                   'multiple': '1'
                               }))
    e_files = forms.FileField(label='Exercise Templates',
                              widget=forms.FileInput(attrs={
                                  'class': 'form-control',
                                  'multiple': '1'
                              }))
