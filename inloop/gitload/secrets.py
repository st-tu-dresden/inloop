from socket import gethostname

from django.utils.crypto import salted_hmac

GITHUB_KEY = salted_hmac("github_hook", gethostname()).hexdigest()
