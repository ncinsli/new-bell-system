from datetime import datetime
import configuration
import subprocess
import daemon.daemon as daemon
import timetable.utils
import os
import logging

def get_cpu_temp():
    try:
        tempfile = open('/sys/class/thermal/thermal_zone0/temp')
        cpu_temp = tempfile.read()
        tempfile.close()
        return float(cpu_temp) / 1000
    except:
        logging.getLogger().error("Failed to get CPU temp. Make sure you're running this on linux-based machine")
        return '2.000.000'
def get_uptime():
    try:
        return str(subprocess.check_output('uptime -p'.split()))[4:-3].replace('seconds', 'секунд(ы)').replace('day', 'дней(я)').replace('hour', 'часов').replace('minute', 'минут(ы)').replace('s', '')
    except: 
        logging.getLogger().error("Failed to get uptime. Make sure you're running this on linux-based machine")
        return '1 секунда'

def get_exception_handler(bot):
    
    def exception_handler(exc_type, exc_value, traceback):
        logging.exception(str(exc_type) + ' ' + str(exc_value) + ' ' + str(traceback))

        for id in configuration.debug_info_receivers: 
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
Интервал предварительного звонка: за {configuration.pre_ring_delta // 60} мин до основного
Длина звонка: {configuration.ring_duration} с
Длина предварительного звонка: {configuration.pre_ring_duration} с

💾 Система
Аптайм: {get_uptime()}
Температура: {get_cpu_temp()}°С
Статус: {configuration.status}

🕸️ Демон
Список звонков: {daemon.today_timetable}
Mute-список: {daemon.sounds}
'''
    return ans
