import shutil
import glob
import os
from os import path
from time import strptime as strpt
from time import strftime as strft

from inloop.settings import BASE_DIR


def get_template_names(task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name)
    # get all java template files for task, e.g. 'template.java'
    return map(path.basename, glob.glob(p + path.sep + '*.java'))


def get_unittest_names(task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name, 'unittests')
    # get all java template files for task, e.g. 'unittest.java'
    return map(path.basename, glob.glob(p + path.sep + '*.java'))


def del_template(f_name, task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name)
    os.remove(path.join(p, f_name))


def del_unittest(f_name, task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name, 'unittests')
    os.remove(path.join(p, f_name))


def del_task_files(task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name)
    shutil.rmtree(p)


def handle_uploaded_unittest(f, task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name, 'unittests')
    if not path.exists(p):
        os.makedirs(p)

    with open(path.join(p, f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def handle_uploaded_exercise(f, task_name):
    p = path.join(BASE_DIR, 'media', 'exercises', task_name)
    if not path.exists(p):
        os.makedirs(p)

    with open(path.join(p, f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def get_task_templates(task_name):
    overview = {}
    p = path.join(BASE_DIR, 'media', 'exercises', task_name)
    # get all java template files for task
    filenames = map(path.basename, glob.glob(p + path.sep + '*.java'))
    # build dict overview
    for fname in filenames:
        with open(path.join(p, fname)) as f:
            overview[fname] = f.read()
    return overview


def get_latest_solution_files(task, username):
    leading_zero = lambda n: str(n) if len(n) > 1 else '0' + str(n)
    max_int_in_dir = lambda p: str(max([int(d) for d in os.listdir(p)]))
    max_t_in_dir = lambda p: max(strpt(d[:5], '%H:%M') for d in os.listdir(p))
    overview = {}
    p = path.join(
        BASE_DIR,
        'media',
        'solutions',
        username,
        task.title)

    year = max_int_in_dir(p)
    p = path.join(p, year)
    month = leading_zero(max_int_in_dir(p))
    p = path.join(p, month)
    day = leading_zero(max_int_in_dir(p))
    p = path.join(p, day)
    time = strft('%H:%M', max_t_in_dir(p))
    p = path.join(p, time + '_' + str(task.id))

    filenames = map(path.basename, glob.glob(p + path.sep + '*.java'))
    for fname in filenames:
        with open(path.join(p, fname)) as f:
            overview[fname] = f.read()

    print (p)
    return overview
