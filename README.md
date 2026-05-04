# corporate-it-python-sharedutils


## Install using
pip install --force-reinstall git+https://$GITHUB_TOKEN@github.com/asyafoek/corporate-it-python-sharedutils.git@main

## Use from python
from corporate_it_python_sharedutils.postgres_utils import get_connection, list_databases
import os 

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")

connection = get_connection(host, port, user, password, dbname)
list_databases(connection)



