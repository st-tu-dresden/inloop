"""
Install the post-receive hook to enable push deployment.
"""
import argparse
from subprocess import check_call as run

ARGS = argparse.ArgumentParser(description=__doc__.strip())
ARGS.add_argument("ssh_host", metavar="[user@]hostname", help="SSH host and optional username")
ARGS.add_argument("remote_name", help="name that should be used for the new remote")
args = ARGS.parse_args()

print("Initializing a bare repository to push to.")
run(["ssh", args.ssh_host, "git init -q --bare ~/inloop.git"])

print("Installing the hook.")
run(["scp", "-q", "support/git-hooks/post-receive", "%s:inloop.git/hooks" % args.ssh_host])

print("Updating the server's clone to pull from the bare repository.")
run(["ssh", args.ssh_host, "cd ~/inloop && git remote set-url origin ~/inloop.git"])

print("Adding remote '%s' to your git repo." % args.remote_name)
run(["git", "remote", "add", args.remote_name, "%s:inloop.git" % args.ssh_host])

print("Done.")
