"""
Install the post-receive hook to enable push deployment.
"""
import argparse
from subprocess import check_call as run

ARGS = argparse.ArgumentParser(description=__doc__.strip())
ARGS.add_argument("ssh_host", metavar="[user@]hostname", help="SSH host and optional username")
ARGS.add_argument("remote_name", help="name that should be used for the new remote")
args = ARGS.parse_args()

# Initialize a bare repository to push to
run(["ssh", args.ssh_host, "git init --bare ~/inloop.git"])

# Install the hook
run(["scp", "support/git-hooks/post-receive", "%s:inloop.git/hooks" % args.ssh_host])

# Update the server's clone to pull from the local bare repository
run(["ssh", args.ssh_host, "cd ~/inloop && git remote set-url origin ~/inloop.git"])

# Add the push-deploy remote
run(["git", "remote", "add", args.remote_name, "%s:inloop.git" % args.ssh_host])
