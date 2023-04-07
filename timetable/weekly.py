import logging
from datetime import datetime
from configurations import configuration
from singletones import connection
import json

cursor = connection.cursor()

def set_weekly(table, sounds, presounds):
    if table == []:
        return 1
    
    start = table[0]
    shifts = []

    weekdays = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    weekday_json = weekdays[datetime.now().weekday()]

    query = f"""DELETE FROM {configuration.db.main}
    WHERE {weekday_json}=1"""
    for i in weekdays:
        if i != weekday_json:
            query += "\nAND " + i + '=0'
    
    try: 
        cursor.execute(query)
        connection.commit()
    except: pass

    for time in table:

        cursor.execute(f"""UPDATE {configuration.db.main}
        SET {weekday_json}=0
        WHERE time="{time}"
        """)

        connection.commit()

    for time in table: # нужно разделение циклов для того, что бы следующая итерация цикла не удаляла запись прошлого(в случае с ипользованием /split, существует два одинаковых звонка)

        sound = sounds[table.index(time)]
        presound = presounds[table.index(time)]

        cursor.execute(f"""INSERT INTO {configuration.db.main}(time, {weekday_json}, muted, sound, presound) VALUES(?, ?, ?, ?, ?)""",
                        [time, 1, 1 if sound == -1 else 0, sound, presound])
        connection.commit()

    for i in range(1, len(table)):
        prev = datetime.strptime(table[i - 1],"%H:%M")
        cur = datetime.strptime(table[i],"%H:%M")

        shift = (cur - prev).seconds // 60
        if shift == 0: shift = "SEQ"
        shifts.append(shift)

    with open('timetable.json', 'r') as file:
        weekly_timetable = json.load(file)
    weekly_timetable[weekday_json]["firstBell"] = table[0]
    for i in range(0, len(weekly_timetable[weekday_json]["shifts"])):
        weekly_timetable[weekday_json]["shifts"][i] = shifts[i]

    for i in range(len(weekly_timetable[weekday_json]["shifts"]), len(shifts)):
        weekly_timetable[weekday_json]["shifts"].append(shifts[i])

    with open('timetable.json', 'wb') as file:
        file.write(json.dumps(weekly_timetable, indent=4, ensure_ascii=False).encode('utf8'))

    return 0
