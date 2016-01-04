"""
Base settings for inloop project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from os.path import dirname, join
from sys import version_info

if version_info[0] < 3:
    raise RuntimeError("INLOOP must be run with Python 3.x")

PROJECT_ROOT = dirname(dirname(dirname(__file__)))
INLOOP_ROOT = join(PROJECT_ROOT, 'inloop')

AUTH_USER_MODEL = 'accounts.UserProfile'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'huey.djhuey',
    'inloop.core',
    'inloop.accounts',
    'inloop.tasks',
    'inloop.gh_import',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'inloop.middleware.VersionInfoMiddleware',
)

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'
ROOT_URLCONF = 'inloop.urls'
WSGI_APPLICATION = 'inloop.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True
FIRST_DAY_OF_WEEK = 1

# URL prefixes for static and media files
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Static file search path
STATICFILES_DIRS = (
    join(PROJECT_ROOT, 'static', 'dist'),
)

# Template search paths
TEMPLATE_DIRS = (
    join(INLOOP_ROOT, 'templates'),
    # otherwise django.contrib.auth won't find the custom templates
    join(INLOOP_ROOT, 'accounts', 'templates')
)

HUEY = {
    'backend': 'huey.backends.redis_backend',
    'name': 'inloop-task-queue'
}

CHECKER = {
    'test_cmd': 'bash -c "cd {taskSlug} && ../gradlew -DsolutionPath={solutionPath} test 2>&1 | tee /mnt/solution/results.txt"',
    'Container': {
        'container_tag': 'docker-test',
        'task_location': '/mnt/checker/task/',
        'gradlew_location': '/mnt/checker/',
        'solution_path': '/mnt/solution/',
        'container_workdir': '/mnt/checker/',
    },
    'Timeouts': {
        # All timeouts in seconds
        'container_execution': 120,
        'container_kill': 5,
        'container_remove': 5,
        'container_build': 180,
    }
}
