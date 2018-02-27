from huey.contrib.djhuey import db_task


@db_task()
def load_tasks_async():
    load_tasks()


def load_tasks():
    ...
