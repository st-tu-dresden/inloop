from django import forms
from tinymce.widgets import TinyMCE


class UserEditorForm(forms.Form):
    content = forms.CharField(
        label='', widget=TinyMCE(attrs={'cols': 100, 'rows': 20})
    )
