from django import forms
from tasks.models import TaskCategory
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


class ManageCategoriesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ManageCategoriesForm, self).__init__(*args, **kwargs)

        for i, tk in enumerate(TaskCategory.objects.all()):
            name = 'category_%s' % i
            self.fields[name] = forms.BooleanField(
                label=tk.name,
                required=False)

    def get_categories(self):
        for key, value in self.cleaned_data.items():
            if key.startswith('category'):
                yield (key, self.fields[key].label, value)


class NewTaskCategoryForm(forms.ModelForm):
    short_id = forms.CharField(
        max_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))

    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }))

    class Meta(object):
        model = TaskCategory
        fields = ('short_id', 'name')


class ExerciseDeletionForm(forms.Form):
    are_you_sure = forms.ChoiceField(
        choices=YESNO_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-control'
        }))


class ExerciseEditForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra_templates = kwargs.pop('extra_templates')
        extra_unittests = kwargs.pop('extra_unittests')
        super(ExerciseEditForm, self).__init__(*args, **kwargs)
        self.fields['e_cat'] = forms.ChoiceField(
            choices=get_task_categories(),
            label='Exercise Category',
            widget=forms.Select(attrs={
                'class': 'form-control'
            }))

        # save templates as BooleanField
        for i, templ in enumerate(extra_templates):
            name = 'template_%s' % i
            self.fields[name] = forms.BooleanField(
                label=templ,
                required=False)

        # save unittests as BooleanField
        for i, unitt in enumerate(extra_unittests):
            name = 'unittest_%s' % i
            self.fields[name] = forms.BooleanField(
                label=unitt,
                required=False)

    def extra_templates(self):
        for key, value in self.cleaned_data.items():
            if key.startswith('template'):
                yield (key, self.fields[key].label, value)

    def extra_unittests(self):
        for key, value in self.cleaned_data.items():
            if key. startswith('unittest'):
                yield (key, self.fields[key].label, value)

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
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control'
        }))
    e_dead_date = forms.DateTimeField(
        initial=tomorrow,
        label='Deadline Date',
        input_formats=['%m/%d/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control'
        }))
    ut_files = forms.FileField(
        label='Unittest Files',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'multiple': '1'
        }))
    e_files = forms.FileField(
        label='Exercise Templates',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'multiple': '1'
        }))


class ExerciseSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
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
