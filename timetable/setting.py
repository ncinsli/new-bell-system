import sqlite3
from configurations import configuration
from singletones import connection

table_override = configuration.db.overrided
table = configuration.db.main

def set_time(items):
    cursor = connection.cursor()

    cursor.execute(f"DELETE FROM {table}")
    connection.commit()
    for key in items.keys():
        values = [key]
        try:
            sql = f'DELETE FROM {table} WHERE time ="{key}"'
            cursor.execute(sql)
        except: # сорян!
            pass

        for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
            if items[key] != None:
                if day in items[key]:
                    values.append(1)
                else:
                    values.append(0)
                if len(items[key]) == 2:
                    if items[key][0] == items[key][1] and items[key][0] == day:
                        values2 = [key.zfill(5)]
                        for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
                            if d != day:
                                values2.append(0)
                            else:
                                break
                        if len(values2) != 8:
                            values2.append(1)
                        if len(values2) != 8:
                            for i in range(8-len(values2)):
                                values2.append(0)
                        #print(values2)
                        cursor.execute(f"""
                            INSERT INTO {table}(time, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday) Values(?, ?, ?, ?, ?, ?, ?, ?)""", values2)
                        connection.commit()
                        continue
            else:
                values = [key.zfill(5), 0, 0, 0, 0, 0, 0, 0] 

        cursor.execute(f"""
            INSERT INTO {table}(time, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday) Values(?, ?, ?, ?, ?, ?, ?, ?)""", values)
        connection.commit()
