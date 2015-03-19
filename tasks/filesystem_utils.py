import os
import glob
from prktmt.settings import BASE_DIR


def delete_template_file(f, task_name):
    path = os.path.join(BASE_DIR, 'media', 'exercises', task_name)
    os.remove(os.path.join(path, f.name))


def delete_unittest_file(f, task_name):
    path = os.path.join(BASE_DIR, 'media', 'exercises', task_name, 'unittests')
    os.remove(os.path.join(path, f.name))


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


def get_task_templates(task_name):
    overview = {}
    path = os.path.join(BASE_DIR, 'media', 'exercises', task_name)
    # get all java template files for task
    filenames = map(os.path.basename, glob.glob(path + os.path.sep + '*.java'))
    # build dict overview
    for fname in filenames:
        with open(os.path.join(path, fname)) as f:
            overview[fname] = f.read()
    return overview
