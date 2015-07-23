import string
from random import SystemRandom

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import models as auth_models
from django.conf import settings
from django.utils import timezone

from inloop.accounts.validators import validate_mat_num


# Activation email text template
ACTIVATION_EMAIL_TEXT = """\
Howdy {username},

Click the following link within the next week to activate your INLOOP account and
receive awesomeness:

  {link}

We're looking forward to seeing you on the site!

Cheers,
Your INLOOP Team
"""


def next_week():
    """To be used as the default activation key expiration time."""
    return timezone.now() + timezone.timedelta(weeks=1)


class CourseOfStudy(models.Model):
    """Represents the course of study of the respective user."""

    name = models.CharField(max_length=50, help_text="The course name", unique=True)

    def __str__(self):
        return self.name


class UserProfile(auth_models.AbstractUser):
    """Extended user model with support for course of studies."""

    # Characters to be used in the activation key
    CHARS = string.ascii_letters + string.digits
    # Length of the random key
    KEY_LENGTH = 40

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # FIXME: use activation key which encodes expiration
    activation_key = models.CharField(
        max_length=KEY_LENGTH,
        help_text="Random key used to verify the user's email"
    )
    key_expires = models.DateTimeField(
        default=next_week,
        blank=True,
        help_text="The key's deprecation time"
    )
    mat_num = models.IntegerField(
        max_length=7,
        help_text="Matriculation Number",
        null=True,
        validators=[validate_mat_num]
    )
    course = models.ForeignKey(CourseOfStudy, null=True)

    def generate_activation_key(self):
        """Generate a secure random key with length and charset specified above."""
        random = SystemRandom()
        self.activation_key = "".join(random.sample(self.CHARS, self.KEY_LENGTH))

    def activate(self):
        success = False
        if self.key_expires > timezone.now():
            self.is_active = True
            success = True

        self.activation_key = ''
        self.save()
        return success

    def send_activation_mail(self):
        link = "{0}accounts/activate/{1}".format(settings.DOMAIN, self.activation_key)
        subject = "INLOOP Activation"
        message = ACTIVATION_EMAIL_TEXT.format(username=self.username, link=link)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email], fail_silently=True)
