from datetime import datetime
import subprocess
import daemon.daemon as daemon
import configuration
import timetable.utils
import utils

access_denied = '❌ Недостаточно прав'
greeting = 'Добрый день!'

resize_incorrect_format = """❌ Введите команду в необходимом формате:
            
/resize lesson 1 +20min 
Удлиняет сегодняшний первый урок на 20 минут

/resize 22.09.2006 break 4 -5min
Укорачивает четвертую перемену на заданную дату на пять минут"""

mute_incorrect_format =  """❌ Введите команду в необходимом формате:
            
/mute 10:40 
Заглушает звонок в 10:40 на сегодня

/mute 22.09.2006 10:40 
Заглушает звонок в 10:40 на заданную дату"""

unmute_incorrect_format = """❌ Введите команду в необходимом формате:
            
/unmute 10:40 
Убирает глушение с звонока в 10:40 на сегодня

/unmute 22.09.2006 10:40 
Убирает глушение с звонока в 10:40 на заданную дату"""

shift_incorrect_format =  """❌ Введите команду в необходимом формате:
            
/shift +10min 
Сдвигает сегодняшнее расписание на 10 минут вперёд

/shift 22.09.2006 -2h
Сдвигает расписание в заданную дату на 2 часа назад"""

pre_ring_incorrect_format = """❌ Введите команду в необходимом формате:
            
/pre_ring_edit 5 
За 5 минут до основного звонка будет подан предварительный
"""

set_timetable_first = """Отправьте файл расписания в формате JSON по одному из шаблонов
        1. Сдвиговой формат(https://docs.github.com/......)
        2. Абсолютный формат(https://docs.github.com/.....)

❗ Обратите внимание, что при применении расписания все изменения на все дни удалятся
        """

lesson_duration_incorrect_format = """❌ Введите команду в необходимом формате:

/lesson_duration -10min
Уменьшает длину всех уроков сегодня на 10 минут

/lesson_duration 22.09.2006 +5min
Увеличивает длину всех уроков на 5 минут в заданный день
"""

break_duration_incorrect_format ="""❌ Введите команду в необходимом формате:

/break_duration -10min
Уменьшает длину всех перемен сегодня на 10 минут

/break_duration 22.09.2006 +5min
Увеличивает длину всех перемен на 5 минут в заданный день
"""

add_receiver_incorrect_format = f"""❌ Введите команду в необходимом формате:

/add_receiver 19291929
Добавляет в слушателей человека с идентификатором 19291929
"""


about = "BrigeBell146 - экземпляр системы BellBrige для МАОУ СОШ №146 с углублённым изучением физики, математики, информатики г. Перми"

def get_state_reply(daemon: daemon.Daemon) -> str: 
    daemon.update_ring_order()
    nearest, table = daemon.order, daemon.today_timetable
    nowEvent = "Off"

    print(nearest)
    if nearest != -1:
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
{current_rings}''' if nowEvent != 'Off' else 'Сегодня уже не будет звонков'

    ans += f'''

⚙️ Конфигурация
Интервал предварительного звонка: за {configuration.pre_ring_delta // 60} мин до основного
Длина звонка: {configuration.ring_duration} с
Длина предварительного звонка: {configuration.pre_ring_duration} с

💾 Система
Аптайм: {utils.get_uptime()}
Температура: {utils.get_cpu_temp()}°С
Статус: {configuration.status}

🕸️ Демон
Список звонков: {daemon.today_timetable}
Mute-список: {daemon.muted_rings}
'''
    return ans
