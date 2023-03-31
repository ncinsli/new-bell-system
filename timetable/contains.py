import sqlite3
from configurations import configuration
from singletones import connection

table_override = configuration.db.overrided
table = configuration.db.main

def contains(id: str) -> bool:
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE userid=?", [id])
    content = cursor.fetchone()
    connection.commit()
    return content is not None

