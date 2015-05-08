import hashlib
import random
import smtplib

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import models as auth_models
from accounts.validators import validate_mat_num
from inloop.settings import DOMAIN


class CourseOfStudy(models.Model):
    '''
    Represents the course of study of the
    respective user.
    '''
    name = models.CharField(
        max_length=50,
        help_text='The course name',
        unique=True)

    def __str__(self):
        return self.name


class UserProfile(auth_models.AbstractUser):
    '''
    Basic user. Already set (min 30 chars):
    Username, First Name, Last Name, E-Mail
    '''

    def __init__(self, *args, **kwargs):
        super(UserProfile, self).__init__(*args, **kwargs)

    activation_key = models.CharField(
        max_length=40
    )

    mat_num = models.IntegerField(
        max_length=7,
        help_text='Matriculation Number',
        null=True,
        validators=[validate_mat_num]
    )
    course = models.ForeignKey(
        CourseOfStudy,
        null=True)

    def generate_activation_key(self):
        sha = hashlib.sha1()
        seed = str(random.random()) + self.username
        sha.update(seed.encode())
        self.activation_key = sha.hexdigest()

    def activate(self):
        self.is_active = True

    def send_activation_mail(self):
        link = DOMAIN + 'accounts/activate/' + self.activation_key
        s_addr = 'inloop@example.com'
        subject = 'INLOOP Activation'
        message = ('Howdy {username},\n\nClick the following link to '
                   'activate your INLOOP account and receive awesomeness:'
                   '\n\n{link}\n\n'
                   'We\'re looking forward to seeing you on the site!'
                   '\n\nCheers,'
                   '\nYour INLOOP Team'
                   ).format(username=self.username, link=link)

        try:
            send_mail(
                subject,
                message,
                s_addr,
                [self.email],
                fail_silently=False)  # To provoke SMTPException
            return True
        except smtplib.SMTPException:
            return False
