from datetime import datetime
from configurations import configuration
import subprocess
import daemon.daemon as daemon
import timetable.utils
import timetable.middleware
import os
import logging
import json
import toml
import time
import random

def get_cpu_temp():
    try:
        tempfile = open('/sys/class/thermal/thermal_zone0/temp')
        cpu_temp = tempfile.read()
        tempfile.close()
        return float(cpu_temp) / 1000
    except:
        #logging.getLogger().error("Failed to get CPU temp. Make sure you're running this on linux-based machine")
        return round(random.uniform(0.0, 100.0), 5)
def get_uptime():
    try:
        return str(subprocess.check_output('uptime -p'.split()))[4:-3].replace('seconds', 'секунд(ы)').replace('day', 'дней(я)').replace('hour', 'часов').replace('minute', 'минут(ы)').replace('s', '')
    except: 
        logging.getLogger().error("Failed to get uptime. Make sure you're running this on linux-based machine")
        return '1 секунда'

def get_uptime_net():
    try:
        return str(subprocess.check_output('uptime -p'.split()))[4:-3]
    except: 
        #logging.getLogger().error("Failed to get uptime. Make sure you're running this on linux-based machine")
        return "Just booted"

def get_exception_handler(bot):
    
    def exception_handler(exc_type, exc_value, traceback):
        logging.exception(str(exc_type) + ' ' + str(exc_value) + ' ' + str(traceback))

        for id in configuration.privileges.receivers: 
            bot.send_message(id, '🌪  Ошибка системы:\n' + str(exc_type) + ' ' + str(exc_value) + ' ' + str(traceback))

    return exception_handler    


def get_state_reply(daemon: daemon.Daemon) -> str: 
    daemon.update_ring_order()
    nearest, table = daemon.order, daemon.today_timetable
    nowEvent = "Off"

    if nearest == 0:
        current_rings = 'Первый звонок прозвенит в ' + table[0]

    elif nearest != -1:
        thisPeriod = 0
        nextPeriod = 0
        nowEvent = "Off"
        if nearest != 0:
            hours, minutes = map(int, table[nearest-1].split(':'))
            difference = list(map(int, timetable.utils.sub_times(table[nearest], hours * 3600 + minutes * 60).split(":")))
            thisPeriod = str(difference[0] * 60 + difference[1]) + " мин"
            if nearest % 2 == 0:
                nowEvent = "перемена"
            else:
                nowEvent = "урок"
        if nearest == len(table)-1:
            nextPeriod = "нисколько"
        else:
            hours, minutes = map(int, table[nearest].split(':'))
            difference = list(map(int, timetable.utils.sub_times(table[nearest+1], hours * 3600 + minutes * 60).split(":")))
            nextPeriod = str(difference[0] * 60 + difference[1]) + " мин"
        if nowEvent == "Off":
            thisPeriod = "нисколько"
        current_rings = ('Текущий ' if nowEvent == 'урок' else 'Текущая ') + nowEvent + ' длится ' + thisPeriod
        
    else:
        current_rings = 'Сегодня больше нет уроков'
    
    ans = f'''🤖 Отчёт от {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

🛎 Состояние звонков: 
''' 

    ans += f'''Следующий звонок в: {table[nearest]}
Сейчас: {nowEvent.capitalize()}
{current_rings}''' if nowEvent != 'Off' else current_rings

    ans += f'''

⚙️ Конфигурация
Интервал предварительного звонка: за {configuration.rings.interval} мин до основного
Длина звонка: {(str(configuration.rings.main) + 'с') if not configuration.rings.auto else 'автоматически'}
Длина предварительного звонка: {(str(configuration.rings.preparatory) + 'с') if not configuration.rings.auto else 'автоматически'}

💾 Система
Аптайм: {get_uptime()}
Температура: {get_cpu_temp()}°С

📟 Статус
{configuration.status}
'''
    return ans

def get_debug_info(daemon: daemon.Daemon):
    return f"""
🕸️ Демон
Список звонков: {daemon.today_timetable}

Список мелодий: {daemon.sounds}

Список мелодий для предварительных звонков: {daemon.presounds}"""

def load_default_timetable(daemon: daemon.Daemon, configuration_only=False):
    with open('timetable.json', 'r') as table_file:
        table = json.loads(table_file.read())
        
        if "format" not in table:
            pass
        old_cfg = configuration.get_instance()

        if "configuration" in table:
            ret = timetable.middleware.rings_configuration_handler(table["configuration"]) # прогружает вкладку configuration, переписывает переменные configuration.py по имеющимся в timetable.json данным
            if ret != 0:
                configuration.set(old_cfg)
        if configuration_only: return

        if table["format"] == "shift":
            returned = timetable.middleware.shift_table_handler(table)
        elif table["format"] == "absolute":
            returned = timetable.middleware.absolute_table_handler(table)
        
        new_timetable, new_muted, new_presounds = timetable.getting.get_time(datetime.now())
        daemon.update(new_timetable, new_muted, new_presounds)

def get_system_stats():
    data = {}
    data["cpu_temp"] = get_cpu_temp()
    data["uptime"] = get_uptime_net()
    data["type"] = "stats"
    if logging.getLogger().root.hasHandlers():
        logfile_path = logging.getLogger().root.handlers[0].baseFilename
        with open(logfile_path) as log_file:
            log_history = log_file.readlines()[-1]
            data["lastlogs"] = log_history
    
    data["lastupdate"] = time.strftime('%d.%m', time.localtime(os.path.getmtime('.')))
    return data