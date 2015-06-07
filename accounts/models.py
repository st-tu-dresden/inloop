import hashlib
import random

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import models as auth_models
from django.conf import settings
from django.utils import timezone as tmz

from accounts.validators import validate_mat_num


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

    new_email = models.EmailField(
        default='',
        blank=True,
        help_text='The user\'s temporary email address waiting to be validated'
    )

    activation_key = models.CharField(
        max_length=40,
        help_text='SHA1 key used to verify the user\'s email'
    )

    key_expires = models.DateTimeField(
        default=tmz.now() + tmz.timedelta(weeks=1),
        blank=True,
        help_text='The key\'s deprecation time')

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
        success = False
        if self.key_expires > tmz.now():
            self.is_active = True
            success = True

        self.activation_key = ''
        self.save()
        return success

    def activate_mail(self):
        success = False
        if self.key_expires > tmz.now():
            self.email = self.new_email
            success = True

        self.new_email = ''
        self.activation_key = ''
        self.save()
        return success

    def send_activation_mail(self):
        link = settings.DOMAIN + 'accounts/activate/' + self.activation_key
        s_addr = 'inloop@example.com'
        subject = 'INLOOP Activation'
        message = ('Howdy {username},\n\nClick the following link within '
                   'the next week to activate your INLOOP account '
                   'and receive awesomeness:\n\n{link}\n\n'
                   'We\'re looking forward to seeing you on the site!'
                   '\n\nCheers,'
                   '\nYour INLOOP Team'
                   ).format(username=self.username, link=link)
        send_mail(
            subject,
            message,
            s_addr,
            [self.email],
            fail_silently=True)

    def send_mail_change_mail(self, new_address):
        self.new_email = new_address
        self.save()
        link = settings.DOMAIN + 'accounts/activate_mail/' + self.activation_key
        s_addr = 'inloop@example.com'
        subject = 'Your new INLOOP mail'
        message = ('Howdy {username},\n\nClick the following link to '
                   'change your INLOOP email address:'
                   '\n\n{link}\n\n'
                   'We\'re looking forward to seeing you on the site!'
                   '\n\nCheers,'
                   '\nYour INLOOP Team'
                   ).format(username=self.username, link=link)
        send_mail(
            subject,
            message,
            s_addr,
            [new_address],
            fail_silently=True)
