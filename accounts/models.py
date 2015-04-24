import hashlib
import random
import smtplib

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import models as auth_models
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
        self.activation_key = self.generate_activation_key()
        self.is_active = False
        super(UserProfile, self).__init__(*args, **kwargs)

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
        self.save()

    def send_activation_mail(self):
        link = 
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
                'Subject here',
                'Here is the message.',
                'from@example.com',
                ['to@example.com'],
                fail_silently=False)
            return True
        except smtplib.SMTPException:
            return False
