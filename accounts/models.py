from django.db import models
from django.contrib.auth import models as auth_models
from accounts.validators import validate_mat_num


class UserProfile(auth_models.AbstractUser):
    '''
    Basic user. Already set (min 30 chars):
    Username, First Name, Last Name, E-Mail
    '''

    mat_num = models.IntegerField(max_length=7, help_text='Matriculation Number', null=True, validators=[validate_mat_num])
