import sqlite3
from configurations import configuration
from singletones import connection 

table = configuration.db.main
table_override = configuration.db.overrided

def deserialize() -> object:
    cursor = connection.cursor()

    cursor.execute(f"SELECT * FROM {table}")
    content = cursor.fetchall() # Strange
    connection.commit()
    return content

