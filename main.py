import os

database_exists = True
if not os.path.exists("database.db"):
    print("[MAIN] No database found.")
    database_exists = False


import json
import sys
import subprocess
from telebot import *
from datetime import datetime
from daemon.daemon import Daemon
from datetime import datetime, timedelta
from configurations import configuration
from daemon import ring_callbacks
import replies.format_tip, replies.results
import utils
import cli

from singletones import connection
import admins.edit
import admins.storage
import admins.validator
import admins.middleware
import logging

from timetable.events import EventType
import timetable.middleware
import timetable.getting
import timetable.setting
import timetable.muting 
import timetable.utils

from communication.manager import NetManager

if not os.path.exists('logs'):
    os.system("mkdir logs")

if not os.path.exists('sounds'):
    os.system("mkdir sounds")
    
log_filename = os.path.join('logs', f'{datetime.now().strftime("%a %d %b %Y %H;%M")}.log')

logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_filename, mode='a'), logging.StreamHandler(sys.stdout)], format='[%(asctime)s] [%(levelname)s] %(message)s')

token = os.environ["TOKEN"]
#token = "5985971016:AAG6iXLG0aDrnsx4JUmy6TKZMFBa2xVJoeo"
bot = TeleBot(token)
bot.parse_mode = 'html'

timetable.middleware.init()
admins.middleware.init()

date_time = datetime.now()
refreshed_timetable, refreshed_soundtable, new_presoundtable = timetable.getting.get_time(datetime(date_time.year, date_time.month, date_time.day))

daemon = Daemon(refreshed_timetable, refreshed_soundtable, new_presoundtable)

daemon.debugger = bot

netmanager = NetManager(configuration.netdevice.host, "Zvonki2023", utils.get_system_stats) # please fix)

@bot.message_handler(commands=["exec"])
def exec(message):
    if message.from_user.username in configuration.privileges.owners:
        try:
            result = subprocess.check_output(message.text[5:].split())
        
            logging.warning(f'@{message.from_user.username} used unsafe command: {message.text[5:]}')
            bot.reply_to(message, result)
        except:
            logging.error(f'@{message.from_user.username} used unsafe command ({message.text[6:]}). It\'s not a Linux machine!')

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["set_status"])
def set_status(message):
    if (admins.validator.check(message)):
        configuration.status = message.text[12:]
        configuration.save()
#       print(overAllStatus)
#       print(subprocess.check_output(message.text[5:].split()))
        logging.info(f'@{message.from_user.username} set status to: {configuration.status}')
        bot.reply_to(message, replies.results.status_ok)

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["state"])
def state(message):
    logging.info(f'@{message.from_user.username} requested system state')
    bot.reply_to(message, utils.get_state_reply(daemon))

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, replies.results.greeting)

@bot.message_handler(commands=["admins"])
def list_admin(message):
    pretty = '🌐  Администраторы\n\n' + '•  @' + str(admins.storage.get()).replace('[', '').replace(']', '').replace(' ', '').replace("'", '').replace(',', '\n•  @')
    bot.send_message(message.chat.id, pretty)

@bot.message_handler(commands=["add_admin"])
def admin_add(message):
    if (admins.validator.check(message)):
        bot.reply_to(message, admins.middleware.add(message))
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["rm_admin"])
def admin_rm(message):
    if (admins.validator.check(message)):
        bot.reply_to(message, admins.middleware.remove(message))
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/instant_ring' and call.message)
def instant_ring_confirm(message):
    duration = configuration.rings.main
    sound = 'Default' # Если звук не предоставлен
    no_duration_state = False # для обработки логики аргументов
#   print(message)
#   bot.delete_message(message.chat.id, message.message_id)
    daemon.instant_ring(duration, sound)

    try:
        duration = '' if duration == configuration.rings.main else (" длиной в " + str(duration) + " секунд")
        melody = ("\nС мелодией: " + "<b>" + sound + "</b>") if sound != "Default" else ""
        
        for id in configuration.privileges.receivers:
            daemon.debugger.send_message(id, f'🛎️  Ручной звонок{duration} подан пользователем @{str(message.from_user.username).lower()} {melody}')
        
        if str(message.from_user.id) not in configuration.privileges.receivers:
            daemon.debugger.send_message(message.from_user.id, f'🛎️  Подан ручной звонок{duration} {melody}', parse_mode='HTML')
   
    except Exception as e: 
        logging.getLogger().error('Unable to notify debug info receivers about manual ring')
        logging.getLogger().exception(e)

@bot.message_handler(commands=["ring"])
def ring(message):
    if admins.validator.check(message):
        duration = configuration.rings.main
        sound = 'Default' # Если звук не предоставлен
        no_duration_state = False # для обработки логики аргументов

        if message.text == '/ring':
            yes = types.InlineKeyboardButton('Подать звонок', callback_data='/instant_ring')
            bot.send_message(message.from_user.id, "<b>Вы уверены?</b>", parse_mode='HTML', reply_markup=types.InlineKeyboardMarkup().add(yes))
            return 

        try:
            space_count = message.text.count(" ")
            args = message.text.split(" ")
            if space_count > 0:
                try:
                    duration = float(args[1])
                except:
                    sound = " ".join(args[1:]).capitalize()
                    no_duration_state = True
            if space_count > 1:
                if not no_duration_state:
                    sound = " ".join(args[2:]).capitalize()
        except: 
            bot.reply_to(message, replies.format_tip.ring)
            return
        
        sound_files = timetable.utils.get_sound_file_list()
        if sound not in sound_files and sound != 'Default':
            bot.reply_to(message, f"❌ Мелодия не прозвенит, потому что она не была загружена\nЗагрузите мелодию при помощи панели /sounds или команды <code>/upload_sound</code> ")
            return
     
        duration = duration if duration <= configuration.rings.maximum else configuration.rings.maximum
        daemon.instant_ring(duration, sound)

        try:
            duration = '' if duration == configuration.rings.main else (" длиной в " + str(duration) + " секунд")
            melody = ("\nС мелодией: " + "<b>" + sound + "</b>") if sound != "Default" else ""
           
            for id in configuration.privileges.receivers:
                daemon.debugger.send_message(id, f'🛎️  Ручной звонок{duration} подан пользователем @{str(message.from_user.username).lower()} {melody}')
            
            if str(message.from_user.id) not in configuration.privileges.receivers:
                daemon.debugger.send_message(message.from_user.id, f'🛎️  Подан ручной звонок{duration} {melody}', parse_mode='HTML')

        except Exception as e: 
            logging.getLogger().error('Unable to notify debug info receivers about manual ring')
            logging.getLogger().exception(e)

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["resize"])
def resize(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.resize)
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: invalid format')
        else:
            res = timetable.middleware.resize(message, daemon)

            bot.send_message(message.from_user.id, res)
            logging.info(f'@{message.from_user.username} resized timetable ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["mute"])
def mute(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: incorrect format')
            bot.reply_to(message, replies.format_tip.mute)
        else:
            logging.info(f'@{message.from_user.username} muted timetable ({message.text})')
            res = timetable.middleware.mute(message, daemon)
            bot.send_message(message.from_user.id, res)
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["mute_all"])
def mute_all(message):
    if (admins.validator.check(message)):
        res = timetable.middleware.mute_all(message, daemon)
        
        bot.send_message(message.from_user.id, res)

        logging.info(f'@{message.from_user.username} muted all day ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["unmute"])
def unmute(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.unmute)
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: incorrect format')
        else:
            res = timetable.middleware.unmute(message, daemon)
            
            bot.send_message(message.from_user.id, res)

            logging.info(f'@{message.from_user.username} muted timetable ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)


@bot.message_handler(commands=["unmute_all"])
def unmute_all(message):
    if (admins.validator.check(message)): 
        res = timetable.middleware.unmute_all(message, daemon)
        
        bot.send_message(message.from_user.id, res)

        logging.info(f'@{message.from_user.username} unmuted all day ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["shift"])
def shift(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.shift)
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: incorrect format')
        else:
            res = timetable.middleware.shift(message, daemon)
            
            bot.send_message(message.from_user.id, res)

            logging.info(f'@{message.from_user.username} shifted timetable ({message.text})')

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)


@bot.message_handler(commands=["set_interval"])
def set_interval(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.set_interval)
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: incorrect format')
        else:
            res = timetable.middleware.set_interval(message)

            logging.info(f'@{message.from_user.username} edited pre-ring interval ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["get_timetable"])
def get_timetable(message):
    timetable.middleware.get_time(bot, message)
    logging.info(f'@{message.from_user.username} requested timetable')

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/get_timetable' and call.message)
def get_timetable_callbacks(call):
    call_data = call.data.split()
    
    dmy = call_data[1].split('.')
    day, month, year = int(dmy[0]), int(dmy[1]), int(dmy[2])
    date = datetime(year, month, day)
    
    bot.parse_mode = 'HTML'
    
    to_out = timetable.middleware.get_time_raw(date)
    
    prev_day = date - timedelta(days=1)
    dmy_prev = f'{prev_day.day}.{prev_day.month}.{prev_day.year}'
    
    next_day = date + timedelta(days=1)
    dmy_next = f'{next_day.day}.{next_day.month}.{next_day.year}'
    
    go_left_button = types.InlineKeyboardButton(text="<", callback_data=f"/get_timetable {dmy_prev}")
    go_right_button = types.InlineKeyboardButton(text=">", callback_data=f"/get_timetable {dmy_next}")
    
    bot.edit_message_text(f"""
    🗓 Расписание на <b>{timetable.utils.get_weekday_russian(date)}, {date.day}</b>:\n\n{to_out}
    """, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().row(go_left_button, go_right_button))

@bot.message_handler(commands=["set_timetable"])
def set_timetable(message):
    if (admins.validator.check(message)):
        bot.reply_to(message, replies.format_tip.set_timetable_first)
        bot.register_next_step_handler(message, get_new_timetable)
        logging.info(f'@{message.from_user.username} requested to change default timetable')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

def get_new_timetable(message):
    returnedMessage = timetable.middleware.set_time(bot, message, daemon)
    bot.reply_to(message, returnedMessage)
    logging.info(f'@{message.from_user.username} changed default timetable')

@bot.message_handler(commands=["about"])
def about(message):
    bot.send_message(message.chat.id, replies.results.about)

@bot.message_handler(commands=["lesson_duration"])
def lesson_duration(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text or message.text.split()[1].isnumeric():
            bot.reply_to(message, replies.format_tip.lesson_duration)
        else:
            timetable.middleware.events_duration(EventType.LESSON, message, daemon)
            
            bot.send_message(message.from_user.id, replies.results.lessonduration_ok)
         
            logging.info(f'@{str(message.from_user.username).lower()} changed lessons duration ({message.text})')

    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["break_duration"])
def break_duration(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.break_duration)
        else:
            timetable.middleware.events_duration(EventType.BREAK, message, daemon)
        
            bot.send_message(message.from_user.id, replies.results.breakduration_ok)
         
            logging.info(f'@{str(message.from_user.username).lower()} changed breaks duration ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')


@bot.message_handler(commands=["add_receiver"])
def add_receiver(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.add_receiver)
        else:
            configuration.privileges.receivers.add(message.text.split()[1])
            configuration.save()
            bot.send_message(message.from_user.id, replies.results.addreceiver_ok)
            logging.info(f'@{str(message.from_user.username).lower()} added debug updated receiver ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["push"])
def push(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.push)
        else:
            result = timetable.middleware.push(message, daemon)
            bot.send_message(message.from_user.id, result)
         
            logging.info(f'@{str(message.from_user.username).lower()} added new ring ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["pop"])
def pop(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.pop)
        else:
            result = timetable.middleware.pop(message, daemon)
                        
            bot.send_message(message.from_user.id, result)
         
            logging.info(f'@{str(message.from_user.username).lower()} removed new ring ({message.text})' if not result else f'@{str(message.from_user.username).lower()} failed to remove new ring ({message.text}): no such')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["get_timetable_json"])
def get_timetable_json(message):
    timetable_file = open('timetable.json')

    bot.send_message(message.chat.id, '```' + ' ' + timetable_file.read() + '```', parse_mode='MarkdownV2')
    timetable_file.close()
    logging.info(f'@{str(message.from_user.username).lower()} requested timetable in json')

@bot.message_handler(commands=["set_sound"])
def set_sound(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.set_sound)
        else:
            result = timetable.middleware.set_sound(message, daemon)
            
            bot.send_message(message.from_user.id, result)
         
            logging.info(f'@{str(message.from_user.username).lower()} set new sound ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["set_pre_sound"])
def set_pre_sound(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.set_sound_pre)
        else:
            result = timetable.middleware.set_sound(message, daemon, is_preparatory=True)

            bot.send_message(message.from_user.id, result)
         
            logging.info(f'@{str(message.from_user.username).lower()} set new presound ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/upload_sound' and call.message)
def upload_sound_callback(call):
    bot.reply_to(call.message, f'🎵 Отправьте звуковой файл', parse_mode='HTML')
    bot.register_next_step_handler(call.message, upload_sound_callback_name)
    logging.info(f'@{call.message.from_user.username} requested to upload sound file')

def upload_sound_callback_name(message):
    bot.reply_to(message, 'Укажите, как называть аудиозапись')

    bot.register_next_step_handler(message, upload_sound_callback_file, message)

def upload_sound_callback_file(message, file):
    try:
        float(message.text)
        bot.reply_to(message, "Недопустимое название аудиозаписи!")
    except:
        promise_id = bot.send_message(message.from_user.id, '🕑 Аудиозапись обрабатывается').id
        res = timetable.middleware.upload_sound(bot, file, message.text)
        bot.edit_message_text(res, message.chat.id, promise_id)

        logging.info(f'@{message.from_user.username} uploaded sound file ' + message.text)

@bot.message_handler(commands=["upload_sound"])
def upload_sound(message):
    if (admins.validator.check(message)):
        if len(message.text.split()) == 1:
            bot.reply_to(message, replies.format_tip.upload_sound)
            return
        else:
            name = ' '.join(message.text.split()[1:]).capitalize()
            bot.register_next_step_handler(message, get_new_sound, name)
            bot.reply_to(message, f'🎵 Отправьте звуковой файл, которому будет присвоено название "<b>{name}</b>"', parse_mode='HTML')
            logging.info(f'@{message.from_user.username} requested to upload sound file')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/upload_default_sound' and call.message)
def upload_default_sound_callback(call):
    bot.reply_to(call.message, f'🎵 Отправьте звуковой файл, который будет проигрываться по умолчанию', parse_mode='HTML')
    bot.register_next_step_handler(call.message, get_new_sound)
    logging.info(f'@{call.message.from_user.username} requested to upload sound file')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/upload_default_pre_sound' and call.message)
def upload_default_pre_sound_callback(call):
    bot.reply_to(call.message, f'🎵 Отправьте звуковой файл, который будет проигрываться по умолчанию на предварительном звонке', parse_mode='HTML')
    bot.register_next_step_handler(call.message, get_new_sound, 'Defaultpre')
    logging.info(f'@{call.message.from_user.username} requested to upload sound file')

@bot.message_handler(commands=["upload_default_sound"])
def upload_default_sound(message):
    if (admins.validator.check(message)):
        if len(message.text.split()) == 1:
            bot.reply_to(message, f'🎵 Отправьте звуковой файл, который будет проигрываться по умолчанию', parse_mode='HTML')
            bot.register_next_step_handler(message, get_new_sound)
            logging.info(f'@{message.from_user.username} requested to upload sound file')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

def get_new_sound(message, name = 'Default'):
    promise_id = bot.send_message(message.from_user.id, '🕑 Аудиозапись обрабатывается').id

    res = timetable.middleware.upload_sound(bot, message, name)

    bot.edit_message_text(res, message.chat.id, promise_id)
    logging.info(f'@{message.from_user.username} uploaded sound file ' + name)

@bot.message_handler(commands=["sounds"])
def sounds(message):
    set_default = types.InlineKeyboardButton(text="Установить мелодию по умолчанию", callback_data="/upload_default_sound")
    set_pre_default = types.InlineKeyboardButton(text="Установить на предварительный звонок", callback_data="/upload_default_pre_sound")
    upload_new = types.InlineKeyboardButton(text="Добавить мелодию в базу", callback_data="/upload_sound")
    bot.send_message(message.from_user.id, timetable.middleware.get_sounds(), reply_markup=types.InlineKeyboardMarkup().add(set_default).add(set_pre_default).add(upload_new))

@bot.message_handler(commands=["dbg"])
def debug_info(message):
    bot.send_message(message.from_user.id, utils.get_debug_info(daemon))

@bot.message_handler(commands=["weekly"])
def weekly_ask(message):
    if (admins.validator.check(message)):
        if len(message.text.split()) == 1:
            yes = types.InlineKeyboardButton(text="Да", callback_data=f"/weekly")
            
            bot.send_message(message.from_user.id, f'''
<b>🗓 Расписание на сегодня</b>:             

{timetable.middleware.get_time_raw(datetime.now())}
            
<b>Установить такое расписание 
на каждый день недели ({timetable.utils.get_weekday_russian(datetime.now())}) ?</b>''', parse_mode='HTML', reply_markup=types.InlineKeyboardMarkup().add(yes))

            logging.info(f'@{message.from_user.username} requested to change timetable on this day of week')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '/weekly' and call.message)
def weekly(message):
    res = timetable.middleware.weekly(message)
    # utils.load_default_timetable(daemon)
    bot.send_message(message.from_user.id, res)

@bot.message_handler(commands=["set_ring_length"])
def set_ring_duration(message):
    if (admins.validator.check(message)):
        length = int(message.text.split()[1])
        if length <= 0: bot.send_message(message.from_user.id, '❌ Длина звонка не может быть меньше или равной нулю') 
        else: 
            configuration.rings.main = length
            configuration.rings.maximum = configuration.rings.maximum if configuration.rings.maximum > length else length
            configuration.save()
            bot.send_message(message.from_user.id, '✅ Длина звонков успешно изменена')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["set_pre_ring_length"])
def set_pre_ring_duration(message):
    if (admins.validator.check(message)):
        length = int(message.text.split()[1])
        if length <= 0: bot.send_message(message.from_user.id, '❌ Длина предварительного звонка не может быть меньше или равной нулю') 
        else: 
            configuration.rings.preparatory = length
            configuration.rings.maximum = configuration.rings.maximum if configuration.rings.maximum > length else length
            configuration.save()
            bot.send_message(message.from_user.id, '✅ Длина предварительных звонков успешно изменена')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["split"])
def split(message):
    if (admins.validator.check(message)):
        time_split = message.text.split()[1:]
        ret = timetable.middleware.split(time_split)
        bot.send_message(message.from_user.id, ret)
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["group"])
def group(message):
    if (admins.validator.check(message)):
        time = message.text.split()[1:]
        res = timetable.middleware.group(time)
        bot.send_message(message.from_user.id, res)
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["set_pre_ring_length"])
def set_pre_ring_duration(message):
    if (admins.validator.check(message)):
        length = int(message.text.split()[1])
        if length <= 0: bot.send_message(message.from_user.id, '❌ Длина предварительного звонка не может быть меньше или равной нулю') 
        else: 
            configuration.rings.preparatory = length
            configuration.rings.maximum = configuration.rings.maximum if configuration.rings.maximum > length else length
            configuration.save()
            bot.send_message(message.from_user.id, '✅ Длина предварительных звонков успешно изменена')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["auto_length"])
def auto_length(message):
    if (admins.validator.check(message)):
        configuration.rings.auto = not configuration.rings.auto
        configuration.save()
        bot.send_message(message.from_user.id, '✅ Теперь длины звонков равны длинам проигрываемых мелодий' if configuration.rings.auto else '✅ Теперь длины звонков задаются пользователем')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["stop"])
def stop(message):
    if (admins.validator.check(message)):
        ring_callbacks.stop_ring()
        bot.send_message(message.from_user.id, '✅ Звонок остановлен')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

print(f"[MAIN] Let's go!")

netmanager.start()
print("[NETMANAGER] initialized")
#print("[NETMANAGER] IS REMOVED IN THIS BUILD")

def thread_exception_handler(args):
    logging.exception(str(args.exc_type) + ' ' + str(args.exc_value) + ' ' + str(args.exc_traceback))
    
    traceback_catched = traceback.format_exc()
    for id in configuration.privileges.receivers: 
        daemon.debugger.send_message(id, '🔥 Критическая ошибка демон-процесса:\n\n' + f'{args.exc_type.__name__}\n\n{traceback_catched}')

daemon.excepthook = thread_exception_handler
 
if configuration.netdevice.verified == 0: # not registered
    try:
        ret, data = netmanager.register(configuration.netdevice.id)
        if ret != 0:
            print("[NETMANAGER] Can't register! Error: " + str(data))
        else:
            configuration.netdevice.id = data["id"]
            configuration.save()

            print("[NETMANAGER] Waiting for registration")

            netmanager.wait_for_registration()
            while netmanager.get_wait_state():
                time.sleep(5)
            
            configuration.netdevice.name = netmanager.get_name()
            configuration.netdevice.verified = True
            configuration.save()
            print("[NETMANAGER] Successful registration!")
            utils.load_default_timetable(daemon, False)
    
    except Exception as e:
        print(e)
        logging.info('No .json file, using default configs which may not be precisient')

else:
    try:
        ret, data = netmanager.login(configuration.netdevice.id, "Zvonki2023")
        
        if ret != 0:
            print("[NETMANAGER] Can't login! Error: " + str(data))
        else:
            print("[NETMANAGER] Successfull auth!")
    except:
        print("[NETMANAGER] Can't login! Server is down")
        threading.Thread(target=netmanager.retry_login, args=(configuration.netdevice.id, "Zvonki2023", ), daemon=True).start()

daemon.start()
print("[DAEMON] initialized")

for owner in configuration.privileges.owners:
    admins.edit.append(owner)

if configuration.cli_mode:
    cli.command_listener.start()
    
bot.infinity_polling(timeout=60)
