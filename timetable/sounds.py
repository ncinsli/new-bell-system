import os
from pydub import AudioSegment # Проверка формата файла
import sqlite3
import calendar
import configuration
import timetable.resizing
from daemon.daemon import Daemon
from datetime import datetime
from telebot import TeleBot
from telebot import types
from timetable.events import EventType
import logging


table_override = configuration.overrided_time_table_name
table = configuration.time_table_name
connection = configuration.connection

def set_sound(date_time: datetime, order):
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
            cursor.execute(f"""
                    INSERT INTO {table_override}(year, month, day, time, muted, sound) VALUES(?, ?, ?, ?, ?, ?) 
                """, [date_time.year, date_time.month, date_time.day, ring_time, 0, 0 if ring_time.split(':') != [str(date_time.hour).zfill(2), str(date_time.minute).zfill(2)] else order])
            connection.commit()
    else:
        cursor.execute(f"""
                UPDATE {table_override}
                SET sound=?
                WHERE year=? AND month=? AND day=? AND time=? 
            """, [order, date_time.year, date_time.month, date_time.day, time_str])
        connection.commit()

    return 0

def set_sound_day(date_time: datetime, order):
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
            cursor.execute(f"""
                    INSERT INTO {table_override}(year, month, day, time, muted, sound) VALUES(?, ?, ?, ?, ?, ?) 
                """, [date_time.year, date_time.month, date_time.day, ring_time, 0, order])
            connection.commit()
    else:
        cursor.execute(f"""
                UPDATE {table_override}
                SET sound=?
                WHERE year=? AND month=? AND day=? 
            """, [order, date_time.year, date_time.month, date_time.day])
        connection.commit()

    return 0

def upload_sound(bot: TeleBot, message, daemon):
    # Загрузка файла
    if message.content_type == 'document':
        try:
            file_name = message.document.file_name
            file_id = message.document.file_name
            file_id_info = bot.get_file(message.document.file_id)

            content = bot.download_file(file_id_info.file_path)
        except:
            return "❌ Ошибка при получении звукового файла!" 
    elif message.content_type == 'audio':
        try:
            file_name = message.audio.file_name
            file_id = message.audio.file_name
            file_id_info = bot.get_file(message.audio.file_id)

            content = bot.download_file(file_id_info.file_path)
        except:
            return "❌ Ошибка при получении звукового файла!" 
    

    sound_path = "./sounds/" + file_name

    if os.path.exists(sound_path):
        return "❌ Звуковой файл с таким именем уже существует!"
    else:
        try:
            with open(sound_path, 'wb') as file:
                file.write(content)
            sound = AudioSegment.from_file(sound_path, file_name[-3::])
            daemon.add_sound(sound)
        except:
            return "❌ Ошибка при чтении звукового файла!"
    return "✅ Звуковой файл успешно записан"