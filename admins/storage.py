import sqlite3
from configurations import configuration
from singletones import connection

table = configuration.db.admin

def contains(id: str) -> bool:

    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE userid=?", [id])
    content = cursor.fetchone()
    connection.commit()

    return content is not None

def get():
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    content = cursor.fetchall()
    connection.commit()

    content = [c[0] for c in content]
    return content