from datetime import datetime
import calendar
from configurations import configuration
from singletones import connection
import sqlite3 

def get_time(date: datetime):    
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT time, muted, sound, presound
        FROM {configuration.db.overrided}
        WHERE day={date.day} 
              AND month={date.month}
              AND year={date.year}
        ORDER BY time
    """)

    content = cursor.fetchall()
    connection.commit()
    
    if content == []:
        # Значит на этот день распространяется обычное расписание
        columnName = calendar.day_name[date.weekday()].capitalize()
        cursor.execute(f"""
            SELECT time, muted, sound, presound
            FROM {configuration.db.main}
            WHERE {columnName}=1
            ORDER BY time
        """)

        content = cursor.fetchall()
        connection.commit()

    prepared_content = []
    sounds = []
    presounds = []
    for time in content:
        prepared_content.append(time[0].zfill(2))
        sounds.append(time[2] if time[1] == 0 else -1)
        presounds.append(time[3] if time[1] == 0 else -1)

    content = list(map(lambda e: str(e).zfill(2), prepared_content))
    return content, sounds, presounds