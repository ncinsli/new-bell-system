import sqlite3
import calendar
from configurations import configuration
import timetable.resizing
from datetime import datetime
from timetable.events import EventType
from singletones import connection

table_override = configuration.db.overrided
table = configuration.db.main

def shift(date: datetime, mins: int):
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT time
        FROM {table_override}
        WHERE year={date.year}
        AND month={date.month}
        AND day={date.day}
    """)
    content = cursor.fetchone()
    connection.commit()

    if content is None:
        # Значит на этот день ищем обычное расписание
        columnName = calendar.day_name[date.weekday()].capitalize()

        cursor.execute(f"""
            SELECT time, muted, sound, presound
            FROM {table}
            WHERE {columnName}=1
        """)
        content = cursor.fetchall()
        connection.commit()

        for copied in content:
            cursor.execute(f"""
                INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?)
            """, [date.year, date.month, date.day, copied[0], copied[1], copied[2], copied[3]])

    timetable.resizing.resize(date, EventType.LESSON, 1, mins * 60)
    