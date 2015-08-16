"""
Expand and copy the configuration files to /etc
"""
import os
import shutil
from os import path

local_conf = {}
with open("local_conf.py") as f:
    exec(f.read(), local_conf)

configs_dir = "support/configs"
install = [
    ("logrotate.conf", "/etc/logrotate.d/inloop", 0o640),
    ("nginx.conf.template", "/etc/nginx/conf.d/inloop.conf", 0o640),
    ("inloop-web.conf.template", "/etc/init/inloop-web.conf", 0o640),
    ("inloop-setup.conf.template", "/etc/init/inloop-setup.conf", 0o640),
    ("inloop-queue.conf.template", "/etc/init/inloop-queue.conf", 0o640),
    ("sudoers.template", "/etc/sudoers.d/inloop", 0o440),
]

print("Installing:")

for src, dest, mode in install:
    print(" - %s" % dest)
    src = path.join(configs_dir, src)
    if src.endswith(".template"):
        with open(src) as s, open(dest, mode="w") as d:
            d.write(s.read() % local_conf)
    else:
        shutil.copyfile(src, dest)
    os.chmod(dest, mode)

print("Ensuring good permissions for local_conf.py")
os.chmod("local_conf.py", 0o640)
shutil.chown("local_conf.py", local_conf["inloop_adm"], local_conf["inloop_run"])

print("Creating %s" % local_conf["media_root"])
os.mkdir(local_conf["media_root"])
shutil.chown(local_conf["media_root"], local_conf["inloop_run"], local_conf["inloop_run"])

print("Done.")
