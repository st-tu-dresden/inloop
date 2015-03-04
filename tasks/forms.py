from django import forms
from tinymce.widgets import TinyMCE


class UserEditorForm(forms.Form):
    content = forms.CharField(
        label='', widget=TinyMCE(attrs={'cols': 100, 'rows': 20})
    )


class ExerciseSubmissionForm(forms.Form):
    # TODO: Add validators for file size, ending and header
    exercise_name = forms.CharField(max_length=100,
                                    widget=forms.TextInput(attrs={
                                        'class': 'form-control'
                                    }))
    unittest_files = forms.FileField(widget=forms.FileInput(attrs={
        'class': 'form-control',
        'multiple': '1'
    }))
    exercise_files = forms.FileField(widget=forms.FileInput(attrs={
        'class': 'form-control',
        'multiple': '1'
    }))
