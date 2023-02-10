from datetime import datetime
import daemon.daemon as daemon
import configuration
import timetable.utils
import utils

access_denied = '❌ Недостаточно прав'
greeting = 'Добрый день!'

about = "Новая Система звонков - инновационная система по работе со школьными звонками с полным управлением из Telegram"

status_ok = '✅ Статус поменян'
addreceiver_ok = '✅ Пользователь добавлен'
lessonduration_ok = '✅ Продолжительность уроков успешно изменена'
breakduration_ok = '✅ Продолжительность перемен успешно изменена'