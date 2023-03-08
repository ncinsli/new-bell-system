try:
    from RPLCD import i2c
    import threading
    from datetime import datetime
    import time
    import timetable.utils as utils
    import configuration

    # lcd options
    lcdmode = 'i2c'
    charmap = 'A00'
    i2c_expander = 'PCF8574'
    cols = 20
    rows = 4
    port = 3
    address = 0x27

    class Display(threading.Thread):
        def __init__(self, table):
            super().__init__()
            self.table = table
            self.reinit = False
            self.need_update = True
            self.last_time = datetime.now().strftime("%H:%M")
            self.status = None
            self.displaying_time_end = None

            self.lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                    cols=cols, rows=rows)
            self.lcd.backlight_enabled = True
            self.initial_output()

        def calculate_nearest(self):
            nowtime = [datetime.now().hour, datetime.now().minute]
            nearest = -1
            for i in range(len(self.table)):
                if int(self.table[i].split(":")[0]) > nowtime[0] or (int(self.table[i].split(":")[0]) == nowtime[0] and int(self.table[i].split(":")[1]) > nowtime[1]):
                    nearest = i
                    break
            return nearest

        def run(self):
            while True:
                time.sleep(configuration.display_delay_time)
                try: 
                    if self.reinit == True:
                        try:
                            self.lcd = i2c.CharLCD(i2c_expander, address, port=port, charmap=charmap,
                                cols=cols, rows=rows)
                            self.reinit = False
                            self.need_update = True
                            self.lcd.cursor_mode = "hide"
                            self.lcd.clear()
                        except: pass
                    self.update_screen()
                except:
                    self.reinit = True
                    self.lcd.close()

        def initial_output(self):
            self.lcd.clear()
            self.lcd.write_string('    Bridge Bell')
            self.lcd.crlf()
            self.lcd.write_string('    Version: 1.2')
            self.lcd.crlf()
            self.lcd.write_string(' Last update: 09.03')
            self.lcd.crlf()
            self.lcd.write_string('        2023')
            self.lcd.crlf()
            time.sleep(5-configuration.display_delay_time)

        def update_screen(self):
            nearest = self.calculate_nearest()
            nowtime = datetime.now()
            timestr = nowtime.strftime("%H:%M")
            disable_status = False
            if self.status != None:
                if self.displaying_time_end != None:
                    if datetime.timestamp(nowtime) > self.displaying_time_end:
                        self.need_update = True

            if self.need_update == False:
                if timestr != self.last_time:
                    self.last_time = timestr
                    self.need_update = True
                else:
                    self.lcd.home()
            if self.need_update == True:
                if nearest != 0:
                    hours, minutes = map(int, self.table[nearest-1].split(':'))
                    difference = list(map(int, utils.sub_times(self.table[nearest], hours * 3600 + minutes * 60).split(":")))
                    thisPeriod = str(difference[0] * 60 + difference[1]) + " min"
                    if nearest % 2 == 0:
                        nowEvent = "Break"
                    else:
                        nowEvent = "Lesson"
                else:
                    nowEvent = "Off"
                if nearest == len(self.table)-1:
                    nextPeriod = "Off"
                else:
                    hours, minutes = map(int, self.table[nearest].split(':'))
                    difference = list(map(int, utils.sub_times(self.table[nearest+1], hours * 3600 + minutes * 60).split(":")))
                    nextPeriod = str(difference[0] * 60 + difference[1]) + " min"
                if nowEvent == "Off":
                    thisPeriod = "Off"
                

                self.lcd.clear()
                self.lcd.write_string(nowtime.strftime('%d.%m.%Y       %a').upper())
                if nearest != 0 and nearest != -1:
                    self.lcd.write_string(f'{nowEvent.upper()}' + ' ' * (7 - len(nowEvent)) + f'{self.table[nearest - 1]} - {self.table[nearest]}')
                elif nearest == -1:
                    self.lcd.write_string(" School day is over")
                else:
                    if len(self.table) > 0:
                        self.lcd.write_string("Day starts at: " + self.table[0])
                    else:
                        self.lcd.write_string("No rings for today")
                    self.lcd.crlf() # delete if lenght of upper string is 20
                if nearest != -1:
                    if self.status != None:
                        if self.displaying_time_end != None:
                            if datetime.timestamp(nowtime) > self.displaying_time_end:
                                self.status = None
                                self.displaying_time_end = None
                            else:
                                self.lcd.write_string(self.status)
                        else:
                            self.lcd.write_string(self.status)
                    else:
                        time_left = utils.format_minutes((int(self.table[nearest].split(":")[0]) * 60 + int(self.table[nearest].split(":")[1])) - (nowtime.hour*60 + nowtime.minute))
                        if time_left[0] > 0:
                            self.lcd.write_string(f"Time left: {time_left[0]} hours ")
                        else:
                            self.lcd.write_string(f"Time left: {time_left[1]} mins")
                    self.lcd.crlf()
                    self.lcd.write_string(f"        {timestr}")
                else:
                    self.lcd.crlf() 
                    self.lcd.write_string("\n")
                    self.lcd.write_string(f"         {timestr}")
            # screen updated!
            self.need_update = False

        
        def update(self, timetable: list, order: int, next_called_timing):
            self.table = timetable
            self.need_update = True
        def next(self, timetable: list, order: int):
            self.table = timetable
            self.need_update = True
        def no_more_rings(self):
            pass

        def set_status(self, msg): # send None to clear status
            self.status = msg
            self.displaying_time_end = None
            self.need_update = True

        def set_temporary_status(self, msg, displaying_time): # displaying time in seconds
            self.status = msg
            self.displaying_time_end = datetime.timestamp(datetime.now()) + displaying_time
            self.need_update = True

except:
    print("You are not running the system on a Pi computer. All GPIO logic will be ignored")