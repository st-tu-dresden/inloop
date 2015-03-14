import os
from prktmt.settings import BASE_DIR


def handle_uploaded_unittest(f, task_name):
    path = os.path.join(BASE_DIR, 'media', 'exercises', task_name, 'unittests')
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def handle_uploaded_exercise(f, task_name):
    path = os.path.join(BASE_DIR, 'media', 'exercises', task_name)
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
