from timetable.events import EventType
from datetime import datetime
import timetable.utils
import timetable.getting
from configurations import configuration
from singletones import connection
import calendar
import sqlite3

table_override = configuration.db.overrided
table = configuration.db.main

def resize(date: datetime, event: EventType, order: int, seconds: int): # -> UserStorage
    cursor = connection.cursor()

    default_timetable = timetable.getting.get_time(date)[0]
    new_timetable = default_timetable[:order - 1]

    for time in default_timetable[order - 1:]:
        result = timetable.utils.sum_times(time, seconds) if seconds >= 0 else timetable.utils.sub_times(time, abs(seconds))
        new_timetable.append(result)

    try:
        dmy = f'{date.year}.{str(date.month).zfill(2)}.{str(date.day).zfill(2)}'
        columnName = calendar.day_name[date.weekday()].capitalize()

        cursor.execute(f"""
                    SELECT muted, sound, presound FROM {table_override}
                    WHERE year={date.year}
                    AND month={date.month}
                    AND day={date.day}
                """)
        res = cursor.fetchall()
        connection.commit()
        if (len(res) == 0):
            cursor.execute(f"""
                SELECT muted, sound, presound FROM {table}
                WHERE {columnName}=1
            """)
            res = cursor.fetchall()
            connection.commit()

            muted = list(map(lambda e: int(e[0]), res))
            sound = list(map(lambda e: e[1], res))
            presound = list(map(lambda e: e[2], res))
        
        else:
            muted = list(map(lambda e: int(e[0]), res))
            sound = list(map(lambda e: e[1], res))
            presound = list(map(lambda e: e[2], res))

        for ring_time in default_timetable:
            cursor.execute(f"""
                    DELETE FROM {table_override}
                    WHERE year={date.year}
                    AND month={date.month}
                    AND day={date.day}
                    AND time="{ring_time}"
                """)
            connection.commit()

        # print('New timetable', new_timetable)
        # print('Muted', muted)
        print(res)
        for i in range(len(new_timetable)):
            cursor.execute(f"""
                    INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                """, [date.year, date.month, date.day, new_timetable[i], muted[i], sound[i], presound[i]])
            connection.commit()

    except sqlite3.IntegrityError:
        print("Time already exits!")
    try:
        connection.commit()
    except:pass

def resize_events(date: datetime, event: EventType, seconds: int):
    cursor = connection.cursor()

    default_timetable = timetable.getting.get_time(date)[0]
    new_timetable = []

    # ('9:00', '9:45', '9:55', '10:40', '10:50', '11:35')
    # ('9:00', '9:35', '9:45', '10:20', '10:30', '11:05')
    # (0, -10, -10, -20, -20, -30, -30, -40, -40)

    delta = [0] if event == EventType.LESSON else [0, 0]
    for i in range(1, len(default_timetable) // 2 + 1):
        delta.append(seconds * i)
        delta.append(seconds * i)

    # print(default_timetable, len(default_timetable))
    # print(delta, len(delta))

    for i in range(len(default_timetable)):
        result = timetable.utils.sum_times(default_timetable[i], delta[i] * 60) if seconds >= 0 else timetable.utils.sub_times(default_timetable[i], abs(delta[i]) * 60)
        new_timetable.append(result)

    #print(new_timetable, len(new_timetable))
    try:
        dmy = f'{date.year}.{str(date.month).zfill(2)}.{str(date.day).zfill(2)}'
        columnName = calendar.day_name[date.weekday()].capitalize()

        cursor.execute(f"""
                    SELECT muted, sound, presound FROM {table_override}
                    WHERE year={date.year}
                    AND month={date.month}
                    AND day={date.day}
                """)
        
        res = cursor.fetchall()
        connection.commit()
        print(res)
        muted = list(map(lambda e: int(e[0]), res))
        sound = list(map(lambda e: e[1], res))
        presound = list(map(lambda e: e[2], res))
        
        if (len(muted) == 0):
            cursor.execute(f"""
                SELECT muted, sound, presound FROM {table}
                WHERE {columnName}=1
            """)

            res = cursor.fetchall()
            connection.commit()

            muted = list(map(lambda e: e[0], res))
            sound = list(map(lambda e: e[1], res))
            presound = list(map(lambda e: e[2], res))

        for ring_time in default_timetable:
            cursor.execute(f"""
                    DELETE FROM {table_override}
                    WHERE year={date.year}
                    AND month={date.month}
                    AND day={date.day}
                    AND time="{ring_time}"
                """)
            connection.commit()

        #print('New timetable', new_timetable)
        #print('Muted', muted)
        for i in range(len(new_timetable)):
            cursor.execute(f"""
                    INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                """, [date.year, date.month, date.day, new_timetable[i], muted[i], sound[i], presound[i]])
            connection.commit()

    except sqlite3.IntegrityError:
        print("Time already exits!")
    try:
        connection.commit()
    except: pass
