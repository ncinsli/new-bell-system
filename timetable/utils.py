from datetime import datetime
import os

days = {0: u"Понедельник", 1: u"Вторник", 2: u"Среда", 3: u"Четверг", 4: u"Пятница", 5: u"Суббота", 6: u"Воскресенье"}

def get_weekday_russian(date_time: datetime):
    return days[date_time.weekday()].lower()

def time_literals_to_seconds(delta): # абревиатуры типа 2m превращает в 120секунд
    in_seconds = "" # функция возращает пустую строку вместо числа в случае, если литералы не верны по формату
    occurence = delta.find(next(filter(str.isalpha, delta)))

    measured_value = int(delta[:occurence])
    measure = delta[occurence:]

    if measure == 's': in_seconds = measured_value
    if measure == 'min': in_seconds = measured_value * 60
    if measure == 'h': in_seconds = measured_value * 3600

    return in_seconds

def is_time_format(time_arg):
    if type(time_arg) != type(""):
        return False
    time_arg = time_arg.split(":")
    if len(time_arg) != 2:
        return False
    try:
        hours = int(time_arg[0])
        minutes = int(time_arg[1])
        if hours > 23 or hours < 0:
            return False
        if minutes > 59 or minutes < 0:
            return False
    except:
        return False
    return True

def sum_times(initial_time: str, seconds: int):
    if seconds == 0: return initial_time
    hours = int(initial_time.split(':')[0])
    minutes = int(initial_time.split(':')[1])
    minutes += seconds // 60

    while minutes >= 60:
        minutes -= 60
        hours += 1

    return f'{hours}:{str(minutes).zfill(2)}'.zfill(5)

def sub_times(initial_time: str, seconds: int):
    if seconds == 0: return initial_time

    delta_mins = seconds // 60

    hours = int(initial_time.split(':')[0])
    minutes = int(initial_time.split(':')[1])
        
    minutes -= delta_mins

    while minutes < 0:
        minutes += 60
        hours -= 1

    return f'{str(hours).zfill(2)}:{str(minutes).zfill(2)}'.zfill(5)

def get_sound_file_list():
    return [i[:-4] for i in os.listdir('sounds')]

def format_minutes(minutes: int):
    hours = minutes // 60
    minutes = minutes - hours * 60
    return [hours, minutes]