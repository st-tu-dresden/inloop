from django.dispatch import Signal

repository_loaded = Signal(providing_args=['repository'])
