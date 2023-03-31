import logging
import admins.edit, admins.storage, admins.validator 
from telebot import TeleBot
from configurations import configuration
from singletones import connection

cursor = connection.cursor()
table = configuration.db.admin

def init():
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table} (
        userid TEXT UNIQUE
    ) 
    """)

    connection.commit()

def add(message):
    if ' ' not in message.text:
        logging.getLogger().error(f'Operation {message.text} cancelled for user @{str(message.from_user.username).lower()}: invalid format')
        return '❌ Если Вы хотите добавить администратора, Вы должны указать его имя пользователя или Telegram ID'
    
    target = message.text.split()[1].replace('@', '')

    if (not admins.storage.contains(target)):
        admins.edit.append(target)
        logging.info(f'@{message.from_user.username} added admin: {message.text.split()[1]}')
        return f'✅ @{target} теперь администратор'

    else:
        logging.getLogger().info(f'@{message.from_user.username} tried to add admin: {message.text.split()[1]}, but there\'s already such')
        return f'❌ @{target} уже администратор'

def remove(message):    
    target = message.text.replace(' ', '')[len('/rm_admin'):].replace('@', '')

    if target == '':
        return '❗️ Если Вы хотите удалить администратора, Вы должны указать его имя пользователя или Telegram ID'
    
    if (admins.storage.contains(target)):
        admins.edit.delete(target)
        logging.getLogger().info(f'@{message.from_user.username} removed admin: {message.text.split()[1]}')
        return f'✅ @{target} теперь не администратор'
    else:
        logging.getLogger().info(f'@{message.from_user.username} tried to remove admin: {message.text.split()[1]}, but there\'s no such')
        return f'❌ @{target} не был администратором'
