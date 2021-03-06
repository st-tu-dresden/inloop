# Task Repository Manual

## Overview

INLOOP publishes tasks by fetching the task instructions, unit tests, and other material that is
necessary to present your tasks from a Git repository. You should not add or modify the tasks in
INLOOP's admin interface (which is automatically generated by Django).

The directory structure of the repository is as follows:

    .
    ├── .dockerignore
    ├── Dockerfile
    ├── Makefile
    ├── task-1/
    │   ├── attachments/
    │   ├── images/
    │   ├── meta.json
    │   └── task.md
    └── task-2/
        ├── attachments/
        ├── images/
        ├── meta.json
        └── task.md

Things to note:

* A task repository must at least contain a `Dockerfile` and a `Makefile`.
* Each task in a task repository resides in its own subdirectory and needs to provide a `meta.json`
  and a `task.md` file.
* Everything else is up to you!

An example of a task repository containing programming assignments in Java can be found at
https://github.com/st-tu-dresden/inloop-java-repository-example.


## Task instructions: task.md

The task text is provided as *Markdown*, in a file called `task.md`. You can design your documents
arbitrarily, there is no limitation whatsoever. You may also freely reference attachments and
images, which reside in their respective subdirectories (*optional*).


## Task metadata: meta.json

Task metadata, such as publication dates or deadlines, are stored as a simple key/value structure
in the `meta.json` file:

```json
{
    "title": "Task title",
    "category": "Category name for this task",
    "pubdate": "2018-03-08 10:00:00 +0200",
    "deadline": "2018-03-08 10:00:00 +0200"
}
```

The `deadline` key is optional.


## Import hook: Makefile

If you need to perform some operations during the import of the task repository, such as generating
files, creating archives, attachments, etc., you can do this in the `Makefile`.

The most simple, no-operation `Makefile` is:

```Makefile
default:
```


## Test image description: Dockerfile

Each task repository must provide a `Dockerfile`. During import, INLOOP will build a container
image according to this specification. The resulting image is expected to be self-contained, and
for each submitted solution, INLOOP will spawn a new container using that image. It must implement
the following interface:

1. The image must provide an entrypoint that accepts the task name (= directory name of the task)
   as one and only argument.

2. A non-zero return code of the entrypoint indicates that the check failed for some reason.
   Possible reasons include: failed compilation, failed unit test, internal error due to
   misconfiguration/crash. A return code of zero, on the other hand, means that the submitted
   solution passed all tests.

3. The image should expect user-submitted files at `/checker/input`, which is a read-only location.
   Caveat: The hierarchy of the dropped files currently is flat, i.e., there are *no*
   subdirectories and there is currently no way to specify them.

4. A spawned container may output diagnostic information via the standard output and error file
   streams, which will be displayed to the user in the "Console output" view.

5. Additional outputs that should be retained by INLOOP may be written to `/checker/output/storage`.
   This is the place where the different execution stages can drop their outputs as files (e.g.,
   unit test result XML files, PMD/SpotBugs reports, …).

6. The rootfs of the container is mounted read-only. Temporary files may be written to
   `/checker/scratch`.
