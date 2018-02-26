Old Git versions on Debian
--------------------------

In its standard installation, Debian 8 ships with Git version 2.1. But the Git import component
of INLOOP relies on support for the `GIT_SSH_COMMAND` environment variable, which has been
introduced in Git 2.3. There are two possible workarounds for this problem:

* Option 1: Install Git from the [backports repository](https://backports.debian.org/Instructions/),
  which provides a more up-to-date version.
* Option 2: Put the following configuration options into the file `$HOME/.ssh/config`, where
  `$HOME` is the home directory of the user that runs the queue (typically `huey`):

      BatchMode yes
      StrictHostKeyChecking no
