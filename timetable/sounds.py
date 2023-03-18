import os
from pydub import AudioSegment 
import sqlite3
import calendar
import configuration
import timetable.resizing
import timetable.middleware
from daemon.daemon import Daemon
from datetime import datetime
from telebot import TeleBot
from telebot import types
from timetable.events import EventType
import logging


table_override = configuration.overrided_time_table_name
table = configuration.time_table_name
connection = configuration.connection

def set_sound(date_time: datetime, name: str, is_preparatory: bool):
    cursor = connection.cursor()
    
    time_str = str(date_time.time())[:5].zfill(5)
    timetable_today = timetable.getting.get_time(date_time)[0]

    cursor.execute(f"""
    SELECT * FROM {table_override}
    WHERE day={date_time.day}
    AND month={date_time.month}
    AND year={date_time.year}
    """)
    overrides = cursor.fetchall()

    connection.commit()

    if len(overrides) == 0:
        # Значит этот день не был особенным, поэтому его надо таковым сделать
        for ring_time in timetable_today:
            cursor.execute(f"""SELECT {'sound' if not is_preparatory else 'presound'} FROM {table} WHERE time="{str(date_time.hour).zfill(2)}:{str(date_time.minute).zfill(2)}"
            """)

            defaults = cursor.fetchone()[0]
            connection.commit()
            
            if not is_preparatory:
                cursor.execute(f"""
                        INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                    """, [date_time.year, date_time.month, date_time.day, ring_time, 0, defaults if ring_time.split(':') != [str(date_time.hour).zfill(2), str(date_time.minute).zfill(2)] else name, "defaultpre"])
            else:
               cursor.execute(f"""
                        INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                    """, [date_time.year, date_time.month, date_time.day, ring_time, 0, "default", defaults if ring_time.split(':') != [str(date_time.hour).zfill(2), str(date_time.minute).zfill(2)] else name]) 
            connection.commit()
    else:
        if not is_preparatory:
            cursor.execute(f"""
                    UPDATE {table_override}
                    SET sound=?
                    WHERE year=? AND month=? AND day=? AND time=? 
                """, [name, date_time.year, date_time.month, date_time.day, time_str])
        else:
            cursor.execute(f"""
                    UPDATE {table_override}
                    SET presound=?
                    WHERE year=? AND month=? AND day=? AND time=? 
                """, [name, date_time.year, date_time.month, date_time.day, time_str])
        connection.commit()

    return 0

def set_sound_day(date_time: datetime, name: str, pre: bool):
    cursor = connection.cursor()

    time_str = str(date_time.time())[:5].zfill(5)
    timetable_today = timetable.getting.get_time(date_time)[0]

    cursor.execute(f"""
    SELECT * FROM {table_override}
    WHERE day={date_time.day}
    AND month={date_time.month}
    AND year={date_time.year}
    """)

    overrides = cursor.fetchall()
    connection.commit()

    if len(overrides) == 0:
        # Значит этот день не был особенным, поэтому его надо таковым сделать
        for ring_time in timetable_today:
            if pre == False:
                cursor.execute(f"""
                        INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                    """, [date_time.year, date_time.month, date_time.day, ring_time, 0, name, "defaultpre"])
            else:
                cursor.execute(f"""
                        INSERT INTO {table_override}(year, month, day, time, muted, sound, presound) VALUES(?, ?, ?, ?, ?, ?, ?) 
                    """, [date_time.year, date_time.month, date_time.day, ring_time, 0, "default", name])
            connection.commit()
    else:
        if pre == False:
            cursor.execute(f"""
                    UPDATE {table_override}
                    SET sound=?
                    WHERE year=? AND month=? AND day=? 
                """, [name, date_time.year, date_time.month, date_time.day])
        else:
            cursor.execute(f"""
                    UPDATE {table_override}
                    SET presound=?
                    WHERE year=? AND month=? AND day=? 
                """, [name, date_time.year, date_time.month, date_time.day])
        connection.commit()

    return 0
