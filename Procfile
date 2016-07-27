web: PYTHONUNBUFFERED=1 python manage.py runserver
redis: redis-server --bind 127.0.0.1 --loglevel warning --dir .state
huey: python manage.py run_huey --workers=2
tests: ./watchmedo_tests
