from datetime import datetime
import configuration
import json

connection = configuration.connection
cursor = connection.cursor()

def set_weekly(table, sounds):
    start = table[0]
    shifts = []
    weekday_json = ("OnMonday", "OnTuesday", "OnWednesday", "OnThursday", "OnFriday", "OnSaturday", "OnSunday")[datetime.now().weekday()]


    cursor.execute(f"""UPDATE {configuration.time_table_name}
    SET {weekday_json}=0
    """)
    connection.commit()

    for time in table:
        sound = sounds[table.index(time)]

        print(f"""UPDATE {configuration.time_table_name}
        SET {weekday_json}=1,
        sound="{sound}"
        WHERE time="{time}"
        """)
        cursor.execute(f"""UPDATE {configuration.time_table_name}
        SET {weekday_json}=1,
        sound="{sound}"
        WHERE time="{time}"
        """)
        connection.commit()

        try:
            cursor.execute(f"""INSERT INTO {configuration.time_table_name}(time, {weekday_json}, sound) VALUES("{time}", 1, "{sound}")""")
            connection.commit()
        except: pass

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

