import sqlite3
from configurations import configuration
from singletones import connection

table_override = configuration.db.overrided
table = configuration.db.main

def delete_all():
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM {table_override}")
    connection.commit()
