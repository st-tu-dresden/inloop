"""
Functional test for provision.py

Be warned: this will take a bit longer! You will need to have vagrant and
the vagrant-box-snapshot plugin installed. Use

  vagrant plugin install vagrant-vbox-snapshot

to install it. The test will destroy any vagrant box you might have and
recreate and provision it from scratch. Afterwards, it will create a snapshot
of the fresh box in order to save some time.

To speed up the test, it will ssh directly into the box (not `vagrant ssh`).
For this to work you need to

  vagrant ssh-config >> ~/.ssh/config

once.

NOTE: The Vagrant box *may* be in an invalid state afterwards.
"""
import sys
import shutil
import subprocess
import unittest
from subprocess import check_call as run, check_output


class PrepareDeployTest(unittest.TestCase):
    snapshot_name = "prepare_deploy_fresh"
    setup_cmd = "sudo python3.4 /vagrant/setup_tools/provision.py --yes /srv/apps"

    @classmethod
    def setUpClass(cls):
        print("Determining if you already have the snapshot '%s'... " % cls.snapshot_name, end='')
        snapshots = check_output(["vagrant", "snapshot", "list"], universal_newlines=True)
        if cls.snapshot_name not in snapshots:
            print("Nope. Destroying the old box.")
            run(["vagrant", "destroy", "--force"])
            print("Creating and provisioning a new box.")
            run(["vagrant", "up"])
            print("Creating snapshot %s" % cls.snapshot_name)
            run(["vagrant", "snapshot", "take", cls.snapshot_name])
        else:
            print("Yep.")
            run(["vagrant", "snapshot", "go", cls.snapshot_name])
        print("Executing the provisioning script.")
        run(["ssh", "precise", cls.setup_cmd])

    @staticmethod
    def vagrant_run(cmd):
        """Execute cmd inside the vagrant box and return the output.

        The output includes stderr.

        Raises AssertionError if the command returns non-zero, meaning you can use
        this function like an assertion (e.g., `vagrant_run("test -r some_file")`).
        """
        # ssh needs to be silenced with -q, otherwise always prints out "Connection ... closed"
        try:
            return check_output(["ssh", "-q", "precise", cmd],
                                stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as exc:
            raise AssertionError(cmd, exc.output) from exc

    def test_created_users(self):
        passwd = self.vagrant_run("cat /etc/passwd")
        self.assertTrue("/srv/apps/inloop:/bin/bash" in passwd)
        self.assertTrue("/srv/apps/inloop-run:/usr/sbin/nologin" in passwd)

    def test_virtualenv(self):
        self.vagrant_run("test -d /srv/apps/inloop/virtualenv")

    def test_sudo_config(self):
        self.vagrant_run("sudo -u inloop -i sudo -n -u inloop-run /bin/true")

    def test_file_owners(self):
        for user in "inloop", "inloop-run":
            # lists files in the directory not owned by the specified user
            aliens = self.vagrant_run(
                "sudo find /srv/apps/{user} -not -user {user}".format(user=user)
            ).strip()
            self.assertEqual("", aliens)

    def test_environment(self):
        env = self.vagrant_run("sudo -u inloop -i env")
        self.assertTrue("VIRTUAL_ENV=" in env)

    @unittest.skip
    def test_psql(self):
        """We should be able to list the available databases w/o specifying a password"""
        # (caused by local "peer" authentification)
        self.vagrant_run("sudo -u inloop -i psql --list")

    def test_copied_keys(self):
        """The ssh keys should exist and be the same."""
        id_rsa = self.vagrant_run("sudo cat /srv/apps/inloop/.ssh/id_rsa").strip()
        with open(".ssh_deploy_key_inloop") as f:
            self.assertEqual(id_rsa, f.read().strip())

        id_rsa = self.vagrant_run("sudo cat /srv/apps/inloop-run/.ssh/id_rsa").strip()
        with open(".ssh_deploy_key_tasks") as f:
            self.assertEqual(id_rsa, f.read().strip())

    def test_copied_auth_keys(self):
        self.vagrant_run("sudo test -f /srv/apps/inloop/.ssh/authorized_keys")


if __name__ == "__main__":
    if not shutil.which("vagrant"):
        sys.exit("Can't find `vagrant`.")
    unittest.main()
