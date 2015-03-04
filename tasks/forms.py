from django import forms
from tinymce.widgets import TinyMCE


class UserEditorForm(forms.Form):
    content = forms.CharField(
        label='', widget=TinyMCE(attrs={'cols': 100, 'rows': 20})
    )


class ExerciseSubmissionForm(forms.Form):
    exercise_name = forms.CharField(max_length=100)
    unittest_files = forms.FileField(widget=forms.FileInput(attrs={
        'multiple': '1'
    }))
    exercise_files = forms.FileField(widget=forms.FileInput(attrs={
        'multiple': '1'
    }))
