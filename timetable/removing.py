import sqlite3
import calendar
import configuration
import timetable.resizing
from datetime import datetime
from timetable.events import EventType


table_override = configuration.overrided_time_table_name
table = configuration.time_table_name
connection = configuration.connection

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
        return 1
    else:
        cursor.execute(f"""
                DELETE FROM {table_override} WHERE time="{time_str}" 
            """)
        connection.commit()

    return 0

    