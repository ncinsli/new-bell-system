import logging
from datetime import datetime
import configuration
import json

connection = configuration.connection
cursor = connection.cursor()

def set_weekly(table, sounds, presounds):
    if table == []:
        return 1
    
    start = table[0]
    shifts = []
    weekday_json = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[datetime.now().weekday()]

    cursor.execute(f"""UPDATE {configuration.time_table_name}
    SET {weekday_json}=0
    """)
    connection.commit()

    for time in table:
        sound = sounds[table.index(time)]
        presound = presounds[table.index(time)]

        cursor.execute(f"""SELECT id FROM {configuration.time_table_name}
            WHERE time="{time}"
        """)
        occurencies = cursor.fetchall()
        connection.commit()

        if len(occurencies) > 0:
            cursor.execute(f"""UPDATE {configuration.time_table_name}
                SET {weekday_json}=1,
                muted={1 if sound == -1 else 0},
                sound="{sound}",
                presound="{presound}"
                WHERE time="{time}"
            """)
            connection.commit()
        else:
            try:
                cursor.execute(f"""INSERT INTO {configuration.time_table_name}(time, {weekday_json}, muted, sound, presound) VALUES(?, ?, ?, ?, ?)""",
                               [time, 1, 1 if sound == -1 else 0, sound, presound])
                connection.commit()
            except Exception as e: 
                logging.getLogger().exception(e)

    for i in range(1, len(table)):
        prev = datetime.strptime(table[i - 1],"%H:%M")
        cur = datetime.strptime(table[i],"%H:%M")

        shifts.append((cur - prev).seconds // 60)

    with open('timetable.json', 'r') as file:
        weekly_timetable = json.load(file)

    weekly_timetable[weekday_json]["firstBell"] = table[0]
    for i in range(0, len(shifts)):
        weekly_timetable[weekday_json]["shifts"][i] = shifts[i]

    with open('timetable.json', 'w') as file:
        file.write(json.dumps(weekly_timetable, indent=4))

    return 0
