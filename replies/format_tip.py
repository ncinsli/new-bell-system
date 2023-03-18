ring = """❌ Введите команду в необходимом формате:
            
/ring 
Ручной звонок с длиной по умолчанию

/ring 1
Ручной звонок длиной в одну секунду"""

resize = """❌ Введите команду в необходимом формате:
            
/resize lesson 1 +20min 
Удлиняет сегодняшний первый урок на 20 минут

/resize 22.09.2006 break 4 -5min
Укорачивает четвертую перемену на заданную дату на пять минут"""

mute =  """❌ Введите команду в необходимом формате:
            
/mute 10:40 
Заглушает звонок в 10:40 на сегодня

/mute 22.09.2006 10:40 
Заглушает звонок в 10:40 на заданную дату"""

unmute = """❌ Введите команду в необходимом формате:
            
/unmute 10:40 
Убирает глушение с звонока в 10:40 на сегодня

/unmute 22.09.2006 10:40 
Убирает глушение с звонока в 10:40 на заданную дату"""

shift =  """❌ Введите команду в необходимом формате:
            
/shift +10min 
Сдвигает сегодняшнее расписание на 10 минут вперёд

/shift 22.09.2006 -2h
Сдвигает расписание в заданную дату на 2 часа назад"""

pre_ring_edit = """❌ Введите команду в необходимом формате:
            
/pre_ring_edit 5 
За 5 минут до основного звонка будет подан предварительный
"""

set_timetable_first = """Отправьте файл расписания в формате JSON по одному из шаблонов
        1. Сдвиговой формат(https://docs.github.com/......)
        2. Абсолютный формат(https://docs.github.com/.....)

❗ Обратите внимание, что при применении расписания все изменения на все дни удалятся
❓ Текущее файловое расписание можно получить командой /get_timetable_json
        """

lesson_duration = """❌ Введите команду в необходимом формате:

/lesson_duration -10min
Уменьшает длину всех уроков сегодня на 10 минут

/lesson_duration 22.09.2006 +5min
Увеличивает длину всех уроков на 5 минут в заданный день
"""

break_duration ="""❌ Введите команду в необходимом формате:

/break_duration -10min
Уменьшает длину всех перемен сегодня на 10 минут

/break_duration 22.09.2006 +5min
Увеличивает длину всех перемен на 5 минут в заданный день
"""

add_receiver = f"""❌ Введите команду в необходимом формате:

/add_receiver 19291929
Добавляет в слушателей человека с идентификатором 19291929
"""

push = f"""❌ Введите команду в необходимом формате:

/push 16:40
Добавляет новый звонок сегодня в 16:40
"""

pop = f"""❌ Введите команду в необходимом формате:

/pop 16:40
Удаляет звонок сегодня в 16:40
"""

set_sound = f"""❌ Введите команду в необходимом формате:

/set_sound 16:40
Устанавливает отправленный пользователем файл на звонок в 16:40

/set_sound 22.09.2006 16:40
Устанавливает отправленный пользователем файл на звонок в 16:40 в заданный день
"""

set_sound_pre = f"""❌ Введите команду в необходимом формате:

/set_sound_pre 16:40
Устанавливает отправленный пользователем файл на предзвонок в 16:40

/set_sound_pre 22.09.2006 16:40
Устанавливает отправленный пользователем файл на предзвонок в 16:40 в заданный день
"""

upload_sound = f"""❌ Введите команду в необходимом формате:
/upload_sound новогодний
+ Загрузите звуковой файл (mp3 / wav)
❓ Загруженнные звуковые файлы можно получить командой /sounds
"""

replace_sound = f"""❌ Введите команду в необходимом формате:
/replace_sound новый_тег
+ Загрузите звуковой файл (mp3 / wav)
"""