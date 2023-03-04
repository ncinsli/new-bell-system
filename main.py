import json
import os
import sys
import subprocess
from telebot import *
from datetime import datetime
from daemon.daemon import Daemon
from datetime import datetime, timedelta
import configuration
import replies.format_tip, replies.results
import utils

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

if not os.path.exists('logs'):
    os.system("mkdir logs")
if not os.path.exists('sounds'):
    os.system("mkdir sounds")
    
log_filename = os.path.join('logs', f'{datetime.now().strftime("%a %d %b %Y %H;%M")}.log')

logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_filename, mode='a'), logging.StreamHandler(sys.stdout)], format='[%(asctime)s] [%(levelname)s] %(message)s')

token = os.environ["TOKEN"]
bot = TeleBot(token)

connection = configuration.connection
cursor = connection.cursor()

timetable.middleware.init()
admins.middleware.init()

date_time = datetime.now()
refreshed_timetable, refreshed_soundtable = timetable.getting.get_time(datetime(date_time.year, date_time.month, date_time.day))

daemon = Daemon(refreshed_timetable, refreshed_soundtable)

daemon.debugger = bot

@bot.message_handler(commands=["exec"])
def exec(message):
    if message.from_user.username in configuration.owners:
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
        admins.middleware.add(bot, message)
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["rm_admin"])
def admin_rm(message):
    if (admins.validator.check(message)):
        admins.middleware.remove(bot, message)
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["ring"])
def ring(message):
    if admins.validator.check(message):
        duration = configuration.ring_duration
        try:
            if message.text != '/ring': duration = float(message.text.split()[1])
        except: 
            bot.reply_to(message, replies.format_tip.ring)
            return
        
        daemon.instant_ring(duration)
        
        try:
            duration = '' if duration == configuration.ring_duration else (" длиной в " + str(duration) + " секунд")
            for id in configuration.debug_info_receivers:
                daemon.debugger.send_message(id, f'🛎️  Ручной звонок{duration} подан пользователем @{str(message.from_user.username).lower()}')

        except: logging.getLogger().error('Unable to notify debug info receivers about manual ring')

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
            timetable.middleware.resize(bot, message, daemon)
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
            timetable.middleware.mute(bot, message, daemon)

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["mute_all"])
def mute_all(message):
    if (admins.validator.check(message)):
        timetable.middleware.mute_all(bot, message, daemon)
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
            timetable.middleware.unmute(bot, message, daemon)
            logging.info(f'@{message.from_user.username} muted timetable ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["unmute_all"])
def unmute_all(message):
    if (admins.validator.check(message)):
        timetable.middleware.unmute_all(bot, message, daemon)
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
            timetable.middleware.shift(bot, message, daemon)
            logging.info(f'@{message.from_user.username} shifted timetable ({message.text})')

    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["pre_ring_edit"])
def pre_ring_edit(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.pre_ring_edit)
            logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: incorrect format')
        else:
            timetable.middleware.pre_ring_edit(bot, message)
            logging.info(f'@{message.from_user.username} edited pre-ring interval ({message.text})')
    else:
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')
        bot.reply_to(message, replies.results.access_denied)

@bot.message_handler(commands=["get_timetable"])
def get_timetable(message):
    timetable.middleware.get_time(bot, message)
    logging.info(f'@{message.from_user.username} requested timetable')

@bot.callback_query_handler(func=lambda call: True)
def get_timetable_callbacks(call):
    if call.message:
        call_data = call.data.split()
        if call_data[0] == '/get_timetable':
        
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
            bot.reply_to(message, replies.lesson_duration)
        else:
            timetable.middleware.events_duration(bot, EventType.LESSON, message, daemon)
            bot.reply_to(message, replies.results.lessonduration_ok)
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
            timetable.middleware.events_duration(bot, EventType.BREAK, message, daemon)
            bot.reply_to(message, replies.results.breakduration_ok)
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
            configuration.debug_info_receivers.add(message.text.split()[1])
            bot.reply_to(message, replies.results.addreceiver_ok)
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
            result = timetable.middleware.push(bot, message, daemon)
            bot.reply_to(message, result)
            logging.info(f'@{str(message.from_user.username).lower()} added new ring ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["pop"])
def push(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.pop)
        else:
            result = timetable.middleware.pop(bot, message, daemon)
            bot.reply_to(message, result)
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
            result = timetable.middleware.set_sound(bot, message, daemon)
            bot.reply_to(message, result)
            logging.info(f'@{str(message.from_user.username).lower()} set new sound ({message.text})')
    else:
        bot.reply_to(message, replies.results.access_denied)    
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

@bot.message_handler(commands=["upload_sound"])
def upload_sound(message):
    if (admins.validator.check(message)):
        if ' ' not in message.text:
            bot.reply_to(message, replies.format_tip.upload_sound)
            bot.register_next_step_handler(message, get_new_sound)
            logging.info(f'@{message.from_user.username} requested to upload sound file')
    else:
        bot.reply_to(message, replies.results.access_denied)
        logging.error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}')

def get_new_sound(message):
    res = timetable.sounds.upload_sound(bot, message, daemon)
    bot.reply_to(message, res)
    logging.info(f'@{message.from_user.username} uploaded sound file')

@bot.message_handler(commands=["sounds"])
def sounds(message):
    bot.reply_to(message, timetable.middleware.get_sounds())

print(f"[MAIN] Let's go!")
daemon.start()

def thread_exception_handler(args):
    logging.exception(str(args.exc_type) + ' ' + str(args.exc_value) + ' ' + str(args.exc_traceback))
    
    traceback_catched = traceback.format_exc()
    for id in configuration.debug_info_receivers: 
        daemon.debugger.send_message(id, '🔥  Критическая ошибка демон-процесса:\n\n' + f'{args.exc_type.__name__}\n\n{traceback_catched}')

daemon.excepthook = thread_exception_handler

if not os.path.exists('database.db'):
    try:
        with open('timetable.json', 'r') as table_file:
            table = json.loads(table_file.read())
        
            if "format" not in table:
                pass

            if table["format"] == "shift":
                returned = timetable.middleware.shift_table_handler(table)
            elif table["format"] == "absolute":
                returned = timetable.middleware.absolute_table_handler(table)
            
            new_timetable, new_muted = timetable.getting.get_time(datetime.now())
            daemon.update(new_timetable, new_muted)

    except:
        logging.info('No .json file, using default configs which may not be precisient')

for owner in configuration.owners:
    admins.edit.append(owner)

bot.infinity_polling()
