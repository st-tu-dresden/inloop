#!/usr/bin/env python
# Helper script that facilitates postgres db initialization
#
# Intended usage:
#   pwgen 20 1 | ./postgres-setup.py inloop - inloop public \
#       | sudo -u postgres -i psql
#
# Explanation of the above example:
#   - Drops existing database "inloop" and role "inloop"
#   - Creates the database "inloop"
#   - Creates unprivileged role "inloop"
#   - Sets a random password read from stdin for role "inloop"
#   - Removes unnecessary privileges

import sys
from string import Template

t = Template('''
\c postgres
DROP DATABASE "$DB_NAME";
CREATE DATABASE "$DB_NAME" WITH TEMPLATE template0;
ALTER DATABASE "$DB_NAME" OWNER TO postgres;

DROP ROLE "$DB_USER";
CREATE ROLE "$DB_USER" NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN;
ALTER ROLE "$DB_USER" ENCRYPTED PASSWORD '$DB_PASS';

REVOKE ALL ON DATABASE "$DB_NAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE "$DB_NAME" TO "$DB_USER";

\c "$DB_NAME"
REVOKE ALL ON SCHEMA "$SCHEMA" FROM PUBLIC;
GRANT CREATE, USAGE ON SCHEMA "$SCHEMA" TO "$DB_USER";
''')

if len(sys.argv) != 5:
    print("Usage: %s dbuser pwfile dbname schema" % sys.argv[0])
    print("  if pwfile is -, read password from stdin")
    sys.exit(1)

if sys.argv[2] == '-':
    pwfile = sys.stdin
else:
    pwfile = open(sys.argv[2])

mapping = {
    'DB_USER': sys.argv[1],
    'DB_PASS': pwfile.read().strip(),
    'DB_NAME': sys.argv[3],
    'SCHEMA': sys.argv[4]
}

print(t.substitute(mapping))
