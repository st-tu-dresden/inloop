"""
Print user and db creation commands suitable to run through `psql`.
"""

local_conf = {}
with open("local_conf.py") as f:
    exec(f.read(), local_conf)

print("""
CREATE ROLE {pg_user} PASSWORD '{pg_pass}' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;
CREATE DATABASE {pg_name} OWNER {pg_user};
""".format(**local_conf))
