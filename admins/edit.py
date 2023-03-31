import os
import sqlite3
from configurations import configuration
from singletones import connection
from admins.status_codes import AppendAdminStatus, DeleteAdminStatus

table = configuration.db.admin

def append(id: str) -> AppendAdminStatus: # -> UserStorage
    id = str(id).replace('@', '').lower()
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            INSERT INTO {table} VALUES(?)
        """, [id])    
        connection.commit()
        return AppendAdminStatus.OK

    except sqlite3.IntegrityError:
        return AppendAdminStatus.USER_ALREADY_EXISTS

def delete(id: str) -> DeleteAdminStatus:
    id = str(id).replace('@', '').lower()    
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            DELETE FROM {table} WHERE userid=?;
        """, [id])    
        connection.commit()    
        return DeleteAdminStatus.OK
    
    except:
        return DeleteAdminStatus.USER_NOT_ADMIN

