"""
Stand-alone script to automate the most common provisioning steps
for new servers.

Use it like this:

  # for a real machine
  ssh root@host python3 - /srv/apps < path/to/provision.py

  # for the Vagrant box
  sudo python3.4 /vagrant/setup_tools/provision.py /srv/apps

It is intended to be run on Ubuntu 12.04 or 14.04. It also assumes
specific packages to be installed. For details please read the the
Vagrantfile.
"""
import argparse
import os
import shutil
import sys
import textwrap
from os import path
from subprocess import check_output as run
from subprocess import CalledProcessError

KEY_README = """\
Please make sure you register the corresponding public keys at

  https://github.com/st-tu-dresden/inloop/settings/keys and
  https://github.com/st-tu-dresden/inloop-tasks/settings/keys

respectively. Please don't enable write access for these keys.
"""

# DevOps username (for the admins/developers)
INLOOP_ADM = "inloop"
# daemon username (used by gunicorn, run_huey, etc.)
INLOOP_RUN = "inloop-run"

ARGS = argparse.ArgumentParser(description=__doc__.strip())
ARGS.add_argument("basedir", help="An absolute path that specifies "
                                  "the home of the INLOOP installation.")
ARGS.add_argument("--yes", action="store_true", help="Non-interactive install. "
                                                     "Assume yes when asked.")


def systemcheck():
    """Check whether the system meets our requirements."""
    for prog in "python3.4", "pyvenv-3.4", "useradd", "ssh-keygen":
        if not shutil.which(prog):
            sys.exit("Can't find `%s` on your PATH." % prog)

    if os.getuid() != 0:
        sys.exit("You need to be root in order to proceed.")


def validate_basedir(dir):
    """Validate the given directory and return a normalized path."""
    dir = path.normpath(dir)
    if dir == "/":
        sys.exit("I refuse to overwrite the root directory.")
    if not path.isabs(dir):
        sys.exit("Please specify an absolute path.")
    if path.exists(dir):
        if not path.isdir(dir):
            sys.exit("%s is not a directory" % dir)
        if os.listdir(dir):
            sys.exit("directory %s is not empty" % dir)
    return dir


def setup_ssh_keys(basedir):
    """Generate the SSH keys.

    If we are on a Vagrant box, we will try to reuse keys from the mounted
    project directory (/vagrant). This will save us useful time and will also
    prevent littering of our Github repository settings.
    """
    ssh_keys = [
        (INLOOP_ADM, "inloop", ".ssh_deploy_key_inloop"),
        (INLOOP_RUN, "inloop-tasks", ".ssh_deploy_key_tasks")
    ]
    fingerprints = []
    for user, reponame, backup_key in ssh_keys:
        key_path = path.join(basedir, user, ".ssh", "id_rsa")
        os.makedirs(path.dirname(key_path), mode=0o700, exist_ok=True)
        backup_path = path.join("/vagrant", backup_key)
        # Please note:
        # - we chown the files once and for all at the end of main()
        # - there's no need to chown inside a VirtualBox shared folder
        if path.isfile(backup_path):
            # Yep, atm we don't care about the public key!
            print("Reusing key from %s" % backup_path)
            shutil.copyfile(backup_path, key_path)
            os.chmod(key_path, 0o600)
        else:
            print("Generating %s." % key_path)
            run(["ssh-keygen", "-q", "-N", "", "-C", reponame, "-f", key_path])
            fingerprints.append(
                run(["ssh-keygen", "-l", "-f", key_path], universal_newlines=True).strip()
            )
            if path.isdir("/vagrant"):
                print("Saving generated key to %s{,.pub}" % backup_path)
                shutil.copyfile(key_path, backup_path)
                shutil.copyfile("%s.pub" % key_path, "%s.pub" % backup_path)
    if fingerprints:
        print(KEY_README)
        print("Fingerprints:")
        for fp in fingerprints:
            print("  %s" % fp)


def main():
    """The main routine."""
    args = ARGS.parse_args()
    systemcheck()
    basedir = validate_basedir(args.basedir)
    os.makedirs(basedir, mode=0o755, exist_ok=True)

    print("I am going to use %s as a basedir." % basedir)
    if not args.yes:
        answer = input("Proceed? [y/N] ")
        if answer.lower() not in ["y", "yes"]:
            sys.exit("Operation cancelled by the user.")

    adm_home = path.join(basedir, INLOOP_ADM)
    try:
        print("Creating the user accounts.")
        run(["useradd", "--create-home", "--home-dir", adm_home,
             "--shell", "/bin/bash", INLOOP_ADM])
        run(["useradd", "--create-home", "--home-dir", path.join(basedir, INLOOP_RUN),
             "--shell", "/usr/sbin/nologin", INLOOP_RUN])
    except CalledProcessError:
        sys.exit("The creation of the user accounts failed.")

    setup_ssh_keys(basedir)

    if path.isdir("/home/vagrant"):
        auth_keys = ".ssh/authorized_keys"
        print("Reusing vagrant's %s" % auth_keys)
        shutil.copyfile(path.join("/home/vagrant", auth_keys), path.join(adm_home, auth_keys))
        os.chmod(path.join(adm_home, auth_keys), 0o600)

    print("Initializing the virtualenv.")
    run(["pyvenv-3.4", path.join(basedir, INLOOP_ADM, "virtualenv")])

    print("Configuring %s's .profile" % INLOOP_ADM)
    with open(path.join(adm_home, ".profile"), mode="a") as profile:
        profile.write("source ~/virtualenv/bin/activate\n")

    print("Configuring sudo.")
    with open("/etc/sudoers", mode="a") as sudoers:
        # on Vagrant, allow to become everyone
        runas = "ALL" if path.isdir("/vagrant") else INLOOP_RUN
        sudoers.write(textwrap.dedent("""
            # Allow the {adm} to become {runas} w/o password
            {adm} ALL=({runas}) NOPASSWD:ALL
        """).format(
            adm=INLOOP_ADM,
            runas=runas
        ))

    for user in INLOOP_ADM, INLOOP_RUN:
        # python has no recursive chown :(
        run(["chown", "-R", "%s:%s" % (user, user), path.join(basedir, user)])


if __name__ == '__main__':
    main()
