import os
import sys
from os import path
from subprocess import check_call as run
from subprocess import call
from time import strftime

os.environ["DJANGO_SETTINGS_MODULE"] = "inloop.settings.production"

local_conf = {}
with open("local_conf.py") as f:
    exec(f.read(), local_conf)

OFFLINE_PAGE = "offline.html"
SNAPSHOTS = path.expanduser("~/db_snapshots")
DATEFMT = "%Y-%m-%d/%H-%M-%S.dump"

print("Initializing paths")
os.makedirs(local_conf['static_root'], exist_ok=True)

print("Enabling maintainance mode")
offline_link = path.join(local_conf['server_root'], OFFLINE_PAGE)
# the src *must* be absolute:
os.symlink(path.join(path.abspath("support"), OFFLINE_PAGE), offline_link)

print("Stopping services")
call(["sudo", "service", "inloop-web", "stop"])

if "--pull" in sys.argv:
    print("Pulling changes")
    run(["git", "pull", "-q", "--ff-only", "origin"])

print("Updating pip and setuptools")
run(["pip", "install", "-q", "--upgrade", "pip", "setuptools"])

print("Installing requirements")
run(["pip", "install", "-q", "-r", "requirements_all.txt"])

print("Precompiling Python sources")
run(["python", "-m", "compileall", "-fq", "inloop"])

print("Collecting static assets")
run(["python", "manage.py", "collectstatic", "--noinput", "-v0"])

print("Precompressing the assets (see nginx' gzip_static directive)")
cmd = "find {static_root} -name '*.{ext}' -print0 | xargs -0 pigz -fknT"
for ext in "js", "css":
    run(cmd.format(static_root=local_conf['static_root'], ext=ext), shell=True)

print("Taking a DB snapshot")
dump_to = path.join(SNAPSHOTS, strftime(DATEFMT))
os.makedirs(path.dirname(dump_to), exist_ok=True)
run(["pg_dump", "--format=custom", "-f", dump_to])

print("Migrating and loading the fixtures")
run(["python", "manage.py", "migrate"])
run(["python", "manage.py", "loaddata", "inloop/fixtures/sites.json"])

print("(Re-)starting services")
call(["sudo", "service", "inloop-web", "start"])

print("Disabling maintainance mode")
os.remove(offline_link)

print("Done.")
