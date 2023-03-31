import sqlite3
import calendar
from configurations import configuration
import timetable.resizing
from datetime import datetime
from timetable.events import EventType
from singletones import connection

table_override = configuration.db.overrided
table = configuration.db.main

def remove(date_time: datetime):
    cursor = connection.cursor()

    time_str = str(date_time.time())[:5].zfill(5)
    timetable_today = timetable.getting.get_time(date_time)[0]

    cursor.execute(f"""
    SELECT * FROM {table_override}
    WHERE time="{time_str}"
    AND day={date_time.day}
    AND month={date_time.month}
    AND year={date_time.year}
    """)

    overrides = cursor.fetchall()

    connection.commit()

    if len(overrides) == 0:
        # Значит этот день не был особенным, поэтому и удалять то нечего

        for ring_time in timetable_today:
            # Мелодия не копируется, потому что звонок все равно будет удален
            cursor.execute(f"""
                    INSERT INTO {table_override}(year, month, day, time, muted) VALUES(?, ?, ?, ?, ?) 
                """, [date_time.year, date_time.month, date_time.day, ring_time, 0])
            connection.commit()    
    
    cursor.execute(f"""
            DELETE FROM {table_override} WHERE time="{time_str}" 
        """)
    connection.commit()

    return 0

    