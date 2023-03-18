from telebot import types
from telebot import TeleBot
from daemon.daemon import Daemon
from datetime import datetime, timedelta

import json
import daemon.ring_callbacks
import timetable.resizing
import os
import timetable.weekly
import timetable.muting
import timetable.adding
import timetable.sounds
import timetable.muting
import timetable.setting
import timetable.getting
import timetable.removing
import timetable.overrides
import timetable.utils as utils
from timetable.events import EventType
import timetable.timetable_defaultvalues as setup
import configuration


INCORRECT_FORMAT_ERROR = "❌ Ошибка при чтении файла. Неверный формат"
connection = configuration.connection
cursor = connection.cursor()
table = configuration.time_table_name
table_override = configuration.overrided_time_table_name

def init():
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
        id INTEGER,
        time TEXT NOT NULL,
        Monday INTEGER DEFAULT 0,
        Tuesday INTEGER DEFAULT 0,
        Wednesday INTEGER DEFAULT 0,
        Thursday INTEGER DEFAULT 0,
        Friday INTEGER DEFAULT 0,  
        Saturday INTEGER DEFAULT 0,
        Sunday INTEGER DEFAULT 0,
        FromDay TEXT DEFAULT "01.09",
        TillDay TEXT  DEFAULT "31.05",
        muted INTEGER DEFAULT 0,
        sound TEXT DEFAULT "default",
        presound TEXT DEFAULT "defaultpre",
        PRIMARY KEY(id AUTOINCREMENT)
    ) 
    """)

    connection.commit()
    cursor.execute(f"""SELECT * FROM {table}""")
    length = len(cursor.fetchall())

    connection.commit()
    if length == 0:
        setup.do_dirty_work()

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_override} (
        id INTEGER,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        day INTEGER NOT NULL,
        time TEXT NOT NULL,
        muted INTEGER DEFAULT 0,
        sound TEXT DEFAULT "default",
        presound TEXT DEFAULT "defaultpre",
        PRIMARY KEY(id AUTOINCREMENT)
    ) 
    """)
    connection.commit()

def get_time_raw(date: datetime):
    # TODO: PRESOUNDS
    list_db, sounds, presounds = timetable.getting.get_time(date)
    combined = []
    # print(list_db, muted)
    for i in range(0, len(list_db) - 1):
        if i % 2 == 0:
            to_append = ('🔇' if sounds[i] == -1 else '') + '<b>• ' + list_db[i] + ' — ' + list_db[i + 1] + '</b>' + ('🔇' if sounds[i + 1] == -1 else '')
        else: to_append = '   ' + ('🔇' if sounds[i] == -1 else '') + list_db[i] + ' — ' + list_db[i + 1] + ('🔇' if sounds[i + 1] == -1 else '')

        combined.append(to_append)

    return (' ' * 4 + '\n').join(combined) if combined != [] else '<b>На этот день нет расписания звонков</b>'

def get_time(bot: TeleBot, message):
    decomposed = message.text.split()
    if len(decomposed) == 1:
        dmy = str(datetime.now().date()).split('-')
    else:
        dmy = (decomposed[1].split('.'))
        dmy.reverse()

    date = datetime(int(dmy[0]), int(dmy[1]), int(dmy[2]))

    bot.parse_mode = 'HTML'

    to_out = get_time_raw(date)

    prev_day = date - timedelta(days=1)
    dmy_prev = f'{prev_day.day}.{prev_day.month}.{prev_day.year}'

    next_day = date + timedelta(days=1)
    dmy_next = f'{next_day.day}.{next_day.month}.{next_day.year}'
    go_left_button = types.InlineKeyboardButton(text="<", callback_data=f"/get_timetable {dmy_prev}")
    go_right_button = types.InlineKeyboardButton(text=">", callback_data=f"/get_timetable {dmy_next}")

    bot.send_message(message.from_user.id, f"""
    🗓 Расписание на <b>{utils.get_weekday_russian(date)}, {date.day}</b>:\n\n{to_out}
    """, reply_markup=types.InlineKeyboardMarkup().row(go_left_button, go_right_button))

def set_time(bot: TeleBot, message, daemon: Daemon):
    try:
        # Свойства файла для загрузки
        file_name = message.document.file_name
        file_id = message.document.file_name
        file_id_info = bot.get_file(message.document.file_id)


        content = bot.download_file(file_id_info.file_path).decode('utf-8')
    except:
        return INCORRECT_FORMAT_ERROR

    #print(content) # Текст файла
    # TODO: Загрузка json -> изменение дефолтной БД (+ скопировать старую, наверное)

    try:
        table = json.loads(content)
    except:
        return INCORRECT_FORMAT_ERROR

    if "format" not in table:
        return INCORRECT_FORMAT_ERROR

    old_configuration = [configuration.pre_ring_delta, 
        configuration.ring_duration, 
        configuration.max_ring_duration,
        configuration.pre_ring_duration,
        configuration.first_pre_ring_enabled,
        configuration.all_pre_rings_enabled]

    if "configuration" in table:
        ret = rings_configuration_handler(table["configuration"]) # прогружает вкладку configuration, переписывает переменные configuration.py по имеющимся в timetable.json данным
        if ret != 0:
            configuration.reset_configuration(old_configuration)
            return INCORRECT_FORMAT_ERROR

    if table["format"] == "shift":
        returned = shift_table_handler(table)
    elif table["format"] == "absolute":
        returned = absolute_table_handler(table)
    else:
        return INCORRECT_FORMAT_ERROR
    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)
    
    with open('timetable.json', 'w') as file:
        file.write(content)
        
    return returned

def rings_configuration_handler(cfg):
    if "preBellTime" in cfg:
        try: 
            preBellTime = utils.time_literals_to_seconds(cfg["preBellTime"])
            if preBellTime != "":
                configuration.pre_ring_delta = preBellTime 
            else:
                return INCORRECT_FORMAT_ERROR
        except: return INCORRECT_FORMAT_ERROR

    if "ringDuration" in cfg:
        try: 
            ringDuration = utils.time_literals_to_seconds(cfg["ringDuration"])
            if ringDuration != "":
                configuration.ring_duration = ringDuration
            else:
                return INCORRECT_FORMAT_ERROR
        except: return INCORRECT_FORMAT_ERROR

    if "preRingDuration" in cfg:
        try: 
            preRingDuration = utils.time_literals_to_seconds(cfg["preRingDuration"])
            if preRingDuration != "":
                configuration.pre_ring_duration = preRingDuration
            else:
                return INCORRECT_FORMAT_ERROR
        except: return INCORRECT_FORMAT_ERROR
    
    if "firstPreRingEnabled" in cfg:
        try: configuration.first_pre_ring_enabled = cfg["firstPreRingEnabled"] 
        except: return INCORRECT_FORMAT_ERROR
    if "allPreRingsEnabled" in cfg:
        try: configuration.all_pre_rings_enabled = cfg["allPreRingsEnabled"] 
        except: return INCORRECT_FORMAT_ERROR
    return 0

def shift_table_handler(table):
    bells = ['08:30', '08:50', '09:00', '09:15', '09:35', '09:45', '09:25', '09:55', '10:10', '10:30', '10:40', '10:20', '10:50', '11:05', '11:35', '11:25', '11:45', '11:55', '12:10', '12:40', '12:30', '12:50', '13:00', '13:15', '13:35', '13:45', '13:25', '13:55', '14:10', '14:30', '14:40', '14:15', '14:50', '15:00', '15:25', '15:35']
    pre_db = dict.fromkeys(bells)

    for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'):
        if "enable" in table[day]:
            if not table[day]["enable"]:
                continue # в этот день звонки отключены
        firstBell = -1
        
        if "firstBell" in table[day]:
            firstBell = table[day]["firstBell"]
        
            if not utils.is_time_format(firstBell):
                return INCORRECT_FORMAT_ERROR

        if firstBell not in bells:
            firstBell = firstBell.zfill(2)
            pre_db[firstBell] = [day]
        
        else:
            if pre_db[firstBell] != None:
                pre_db[firstBell].append(day)
            
            else:
                pre_db[firstBell] = [day]

        if "shifts" in table[day]:
            for b in table[day]["shifts"]:
                if type(b) != type(0):
                    return INCORRECT_FORMAT_ERROR
            last = firstBell
            for b in table[day]["shifts"]:
                last = utils.sum_times(last, b*60)
                if last not in pre_db.keys():
                    pre_db[last] = [day]
                else:
                    if pre_db[last] != None:
                        pre_db[last].append(day)
                    else:
                        pre_db[last] = [day]
        else:
            return INCORRECT_FORMAT_ERROR

    pre_db_items = sorted(list(map(lambda e: (e[0].zfill(5), e[1]), pre_db.items())))

    timetable.overrides.delete_all()
    timetable.setting.set_time(dict(pre_db_items))

    return "✅ Расписание успешно перезаписано"

def absolute_table_handler(table):
    bells = ['08:30', '08:50', '09:00', '09:15', '09:35', '09:45', '09:25', '09:55', '10:10', '10:30', '10:40', '10:20', '10:50', '11:05', '11:35', '11:25', '11:45', '11:55', '12:10', '12:40', '12:30', '12:50', '13:00', '13:15', '13:35', '13:45', '13:25', '13:55', '14:10', '14:30', '14:40', '14:15', '14:50', '15:00', '15:25', '15:35']
    pre_db = dict.fromkeys(bells)

    for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'):
        if "enable" in table[day]:
            if table[day]["enable"] == False:
                continue # в этот день звонки отключены

        if "bells" in table[day]:
            for b in table[day]["bells"]:
                a = b.zfill(5)
                if a not in pre_db.keys():
                    pre_db[a] = [day]
                else:
                    if pre_db[a] != None:
                        pre_db[a].append(day)
                    else:
                        pre_db[a] = [day]
        else:
            return INCORRECT_FORMAT_ERROR

    timetable.overrides.delete_overrides()
    timetable.setting.set_time(dict(sorted(pre_db.items())))

    return "✅ Расписание успешно перезаписано"

def resize(message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    delta = args[0]
    event_type = args[0]
    order = args[1]
    delta = args[2]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
       
        event_type = args[1]
        order = args[2]
        delta = args[3]

    order = int(order)
    date = datetime(year, month, day)
    
    in_seconds = utils.time_literals_to_seconds(delta)
    if in_seconds == "":
        return "❌ Неверное время"

    if event_type == 'lesson':
        timetable.resizing.resize(date, EventType.LESSON, order * 2, in_seconds)

    if event_type == 'break':
        timetable.resizing.resize(date, EventType.BREAK, order * 2 + 1, in_seconds)

    new_timetable, new_sounds, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_sounds, new_presounds)

    return f"{'✅ Урок' if event_type == 'lesson' else 'Перемена'} № {order} теперь {'длиннее' if in_seconds > 0 else 'короче'} на {abs(in_seconds) // 60} минут(ы)"

def shift(message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    delta = args[0]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
        delta = args[1]

    in_seconds = 0
    postfix_index = delta.find(next(filter(str.isalpha, delta)))

    measured_value = int(delta[:postfix_index])
    postfix = delta[postfix_index:]

    if postfix == 'min': in_seconds = measured_value * 60
    if postfix == 'h': in_seconds = measured_value * 3600

    timetable.shifting.shift(datetime(year, month, day), in_seconds // 60)

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)

    return f'✅ Расписание на {utils.get_weekday_russian(datetime(year, month, day))}, {str(day).zfill(2)} {str(month).zfill(2)}, {year} сдвинуто на {in_seconds // 60} мин'

# /mute dd.mm.yyyy hh:mm
def mute(message, daemon: Daemon):
    args = message.text.split()[1:]
    
    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    number = args[0]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
        number = args[1]

    hour = int(number.split(':')[0])
    minutes = int(number.split(':')[1])

    # Сериализация
    timetable.muting.mute(datetime(year, month, day, hour, minutes))

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)

    return f'✅ Звонок в {str(hour).zfill(2)}:{str(minutes).zfill(2)} {str(day).zfill(2)}.{str(month).zfill(2)}.{year} не будет включён'

# /mute dd.mm.yyyy hh:mm
def mute_all(message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])

    # Сериализация
    timetable.muting.mute_all(datetime(year, month, day))

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)

    return f'✅ Все звонки {str(day).zfill(2)}.{str(month).zfill(2)}.{year} будут заглушены'

def unmute(message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    number = args[0]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
        number = args[1]

    hour = int(number.split(':')[0])
    minutes = int(number.split(':')[1])

    # Сериализация
    timetable.muting.unmute(datetime(year, month, day, hour, minutes))

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)
    
    return f'✅ Звонок в {str(hour).zfill(2)}:{str(minutes).zfill(2)} {day}.{month}.{year} будет включён'

# /mute dd.mm.yyyy hh:mm
def unmute_all(message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])

    # Сериализация
    timetable.muting.unmute_all(datetime(year, month, day))

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)

    return f'✅ Все звонки {str(day).zfill(2)}.{str(month).zfill(2)}.{year} будут включены'

def pre_ring_edit(message):
    args = message.text.split()[1:]
    delta_min = int(args[0])

    if delta_min <= 0: return
    
    configuration.pre_ring_delta = delta_min * 60
    return f'✅ Интервал изменён на {delta_min} минут'

def events_duration(affected_events: EventType, message, daemon: Daemon):
    args = message.text.split()[1:]

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    delta = args[0]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
        delta = args[1]

    in_seconds = 0
    postfix_index = delta.find(next(filter(str.isalpha, delta)))

    measured_value = int(delta[:postfix_index])
    postfix = delta[postfix_index:]

    if postfix == 'min': in_seconds = measured_value * 60
    if postfix == 'h': in_seconds = measured_value * 3600

    timetable.resizing.resize_events(datetime(year, month, day), affected_events, in_seconds // 60)

    new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
    daemon.update(new_timetable, new_muted, new_presounds)

def push(message, daemon: Daemon):
    args = message.text.split()[1:]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])

        ring_time = args[1].split(':')
        
        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])

    else:
        day = datetime.now().day
        month = datetime.now().month
        year = datetime.now().year
        
        ring_time = args[0].split(':')
        
        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])

    if ring_h > 23 or ring_h < 0 or ring_m > 59 or ring_m < 0:
        return "❌ Неверное время" 

    res = timetable.adding.add(datetime(year, month, day, ring_h, ring_m))

    if not res:
        new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
        daemon.update(new_timetable, new_muted, new_presounds)

    return "✅ Звонок добавлен" if not res else "❌ Такой звонок уже есть"

def pop(message, daemon: Daemon):
    args = message.text.split()[1:]

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])

        ring_time = args[1].split(':')
        
        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])

    else:
        day = datetime.now().day
        month = datetime.now().month
        year = datetime.now().year
        
        ring_time = args[0].split(':')
        
        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])
        
    if ring_h > 23 or ring_h < 0 or ring_m > 59 or ring_m < 0:
        return "❌ Неверное время" 

    res = timetable.removing.remove(datetime(year, month, day, ring_h, ring_m))
    
    if not res:
        new_timetable, new_sounds, new_presounds = timetable.getting.get_time(datetime.now())
        daemon.update(new_timetable, new_sounds, new_presounds)

    return "✅ Звонок удалён" if not res else "❌ Такого звонка не было"


def set_sound(message, daemon: Daemon, pre: bool):
    args = message.text.split()[1:]
    sound_files = utils.get_sound_file_list()
    print(sound_files)

    if '.' in message.text:
        day = int(args[0].split('.')[0])
        month = int(args[0].split('.')[1])
        year = int(args[0].split('.')[2])
        
        if ':' not in message.text:
            name = ' '.join(args[1:]).strip()

            if name not in sound_files: 
                return f"❌ Мелодия не добавлена на звонок, потому что она не была загружена\nЗагрузите мелодию при помощи панели /sounds или команды <code>/upload_sound {name}</code> "

            res = timetable.sounds.set_sound_day(datetime(year, month, day), name, pre)
            
            if not res:
                new_timetable, new_sounds, new_presounds = timetable.getting.get_time(datetime.now())
                daemon.update(new_timetable, new_sounds, new_presounds)
            
            return "✅ Мелодия добавлена на звонок" if not res else "❌ Мелодия не добавлена на звонок"

        ring_time = args[1].split(':')
        name = ' '.join(args[2:]).strip()

        if name not in sound_files: 
            return f"❌ Мелодия не добавлена на звонок, потому что она не была загружена\nЗагрузите мелодию при помощи панели /sounds или команды <code>/upload_sound {name}</code> "
        
        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])

    else:
        day = datetime.now().day
        month = datetime.now().month
        year = datetime.now().year

        if ':' not in message.text:
            name = ' '.join(args[0:]).strip()

            if name not in sound_files: 
                return f"❌ Мелодия не добавлена на звонок, потому что она не была загружена\nЗагрузите мелодию при помощи панели /sounds или команды <code>/upload_sound {name}</code> "
            
            res = timetable.sounds.set_sound_day(datetime(year, month, day), name, pre)
           
            if not res:
                new_timetable, new_sounds, new_presounds = timetable.getting.get_time(datetime.now())
                daemon.update(new_timetable, new_sounds, new_presounds)

            return "✅ Мелодия добавлена на звонок" if not res else "❌ Мелодия не добавлена на звонок"

        name = ' '.join(args[1:]).strip()

        if name not in sound_files: 
            return f"❌ Мелодия не добавлена на звонок, потому что она не была загружена\nЗагрузите мелодию при помощи панели /sounds или команды <code>/upload_sound {name}</code> "

        ring_time = args[0].split(':')

        ring_h = int(ring_time[0])
        ring_m = int(ring_time[1])
        
    if ring_h > 23 or ring_h < 0 or ring_m > 59 or ring_m < 0:
        return "❌ Неверное время" 

    res = timetable.sounds.set_sound(datetime(year, month, day, ring_h, ring_m), name, pre)
    
    if not res:
        new_timetable, new_sounds, new_presounds = timetable.getting.get_time(datetime.now())
        daemon.update(new_timetable, new_sounds, new_presounds)

    return "✅ Мелодия добавлена на звонок" if not res else "❌ Такого звонка не было"

def get_sounds_last_id():
    sounds = os.listdir(os.path.abspath('sounds'))

    if len(sounds) > 0: 
        return int(sounds[-1].split()[0][1:-1])
    
    else: return -1

def get_sounds():

    sounds = os.listdir(os.path.abspath('sounds'))
    if len(sounds) == 0:
        return '🎵 <b>Нет загруженных мелодий</b>'
    ret = "🎵 <b>Загруженные мелодии</b>\n\n"
    
    for i in range(0, len(sounds)):
        sounds[i] = sounds[i][:-4]

    if 'Default' in sounds:
        ret += f"<b>Мелодия по умолчанию</b>\n"
        sounds.remove('Default')
    
    else: ret += f"<b>Нет мелодии по умолчанию</b>\n"


    for i in range(0, len(sounds)):
        ret += f"{i + 1}. {sounds[len(sounds) - i - 1]}\n"
    
    return ret

def upload_sound(bot: TeleBot, message, name: str):
    file_name = None

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
            file_name = str(message.audio.file_name)
            file_id = message.audio.file_name
            file_id_info = bot.get_file(message.audio.file_id)
            content = bot.download_file(file_id_info.file_path)
        except:
            return "❌ Ошибка при получении звукового файла!" 
    
    
    sound_path = f"./sounds/{name.capitalize()}.{file_name[-3:]}"

    if os.path.exists(sound_path) and name != 'default':
        return "❌ Звуковой файл с таким именем уже существует!"
    else:
        try:
            with open(sound_path, 'wb') as file:
                file.write(content)

            daemon.ring_callbacks.load_sound(sound_path)

        except Exception as e:
            print(e)
            return "❌ Ошибка при чтении звукового файла!"
        
    return "✅ Звуковой файл успешно записан"

def weekly(message):
    table, sounds, presounds = timetable.getting.get_time(datetime.now())

    print(sounds)
    print(presounds)
    timetable.weekly.set_weekly(table, sounds, presounds)

    return '✅ Постоянное расписание обновлено'