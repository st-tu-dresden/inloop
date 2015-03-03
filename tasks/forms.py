from django import forms
from tinymce.widgets import TinyMCE


class UserEditorForm(forms.Form):
    content = forms.CharField(
        label='', widget=TinyMCE(attrs={'cols': 100, 'rows': 20})
    )


class ExerciseSubmissionForm(forms.Form):
    unittest_files = forms.FileField(widget=forms.FileInput(attrs={
        'multiple': '1'
    }))
    exercise_files = forms.FileField(widget=forms.FileInput(attrs={
        'multiple': '1'
    }))
