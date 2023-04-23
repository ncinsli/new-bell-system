try: 
    from displaying.LCD_2004 import Display
except: pass


import sys
import logging
import threading
import os
import traceback
import daemon.utils as utils
import telebot
import time
import timetable.utils
from configurations import configuration
from datetime import datetime
import daemon.ring_callbacks as ring_callbacks

class Daemon(threading.Thread):
    today_timetable: list
    sounds: list
    presounds: list
    order = 0
    last_called_timing: str = '00:00'
    next_called_timing: str = '00:00'
    gpio_mode = False
    debugger : telebot.TeleBot
    day: int

    def __init__(self, table, muted, presounds):
        super().__init__()

        log_filename = os.path.join('logs', f'{datetime.now().strftime("%a %d %b %Y %H;%M;%S")}.log')
        
        self.daemon = True
        self.update(table, muted, presounds)
        self.day = datetime.now().day
        
        if (os.system(f'echo 1 > /sys/class/gpio/gpio{configuration.daemon.port}/value && echo 0 > /sys/class/gpio/gpio{configuration.daemon.port}/value') == 0):
            self.gpio_mode = True

        logging.info(f'GPIO_MODE: {self.gpio_mode}')
        
        ring_callbacks.init()
        self.update_ring_order()

        try: 
            self.display = Display(table)
            self.display.start()

        except: print("[Display] Can't initialize!")

    def update_ring_order(self):
        self.order = utils.nearest_forward_ring_index(self.today_timetable)
        logging.info(f'Updated ring order to: {self.order}')

    def update(self, new_timetable, new_muted, new_presounds):
        self.today_timetable, self.sounds, self.presounds = new_timetable, new_muted, new_presounds # Обращаться к sqlite из другого потока нельзя
        self.today_timetable = list(map(lambda e: e.zfill(5), self.today_timetable))
        
        try: self.display.update(self.today_timetable, self.order, self.next_called_timing)
        except: print("[GPIO] .update")
        timetable_str = str(self.today_timetable).replace("'", "")
        logging.info(f'Updated timetable: {timetable_str}')
        logging.info(f'Updated sound list: {str(self.sounds)}')
        logging.info(f'Updated presound list: {str(self.presounds)}')

    def run(self):
        while True:
            time.sleep(configuration.daemon.delay)
            timing = str(datetime.now().time())[:5]
            timing_forward = timetable.utils.sum_times(timing, configuration.rings.interval * 60)

            if (timing == '00:00' and datetime.now().day != self.day): 
                self.update(*timetable.getting.get_time(datetime.now()))
                self.day = datetime.now().day

            if (timing in self.today_timetable and timing != self.last_called_timing):
                self.order += 1

                self.order = self.today_timetable.index(str(datetime.now().time())[:5])
                logging.info(f'It is an event: order is now {self.order}')

                if self.sounds[self.order] != -1:
                    logging.warn(f'Started ring for {configuration.rings.main} seconds | Melody {self.sounds[self.order]}')
                    
                    ring_callbacks.ring(self.sounds[self.order], configuration.rings.main)
                    logging.warn(f'Stopped ring')

                    self.last_called_timing = timing

                    try:
                        for id in configuration.privileges.receivers:
                            self.debugger.send_message(id, '🛎️  Звонок по расписанию успешно подан')
                    except Exception as e: 
                        logging.error("Unable to notify debug info receivers about the ring")
                        logging.exception(e)

                else:
                    logging.warn(f'No ring (muted)')
                    self.last_called_timing = timing
                    try:
                        for id in configuration.privileges.receivers:
                            self.debugger.send_message(id, '🚫 Звонок по расписанию заглушен и не подан')
                    except Exception as e: 
                        logging.error("Unable to notify debug info receivers about the muted ring. Error is below")
                        logging.exception(e)

                tempIdx = self.today_timetable.index(timing)
                if tempIdx != len(self.today_timetable)-1:
                    self.next_called_timing = self.today_timetable[tempIdx+1]

                    try: self.display.next(self.today_timetable, tempIdx+1)
                    except: print("[GPIO] .next")

                else:
                    self.next_called_timing = "-1" # no more rings for today
                    
                    try: self.display.no_more_rings()
                    except: print("[GPIO] .no_more_rings")

                    logging.warn(f'No more rings')
                
                    try:
                        for id in configuration.privileges.receivers:
                            self.debugger.send_message(id, '⏰ Сегодня больше нет звонков')
                    except: logging.error("Unable to notify debug info receivers about the ending of all rings")


                if self.order + 1 <= len(self.today_timetable) - 1:
                    if self.today_timetable[self.order+1] == self.today_timetable[self.order]:
                        try: self.display.next(self.today_timetable, self.order+1)
                        except: print("[GPIO] .next")

            if (timing_forward in self.today_timetable and timing != self.last_called_timing):
                self.order = self.today_timetable.index(timing_forward)

                if self.order % 2 != 0: continue
                if self.order == 0:
                    if not configuration.rings.first_preparatory_enabled:
                        continue
                else:
                    if not configuration.rings.preparatory_enabled:
                        continue

                if self.presounds[self.order] != -1:
                    logging.warn(f'Started pre-ring for {configuration.rings.preparatory} seconds')

                    ring_callbacks.ring(self.presounds[self.order], configuration.rings.preparatory)
                    
                    logging.warn(f'Stopped pre-ring')

                    try:
                        for id in configuration.privileges.receivers:
                            self.debugger.send_message(id, '🧨  Предзвонок по расписанию успешно подан')
                   
                    except Exception as e: 
                        logging.error("Unable to notify debug info receivers about pre-ring. The exception is below")
                        logging.exception(e)

                    self.last_called_timing = timing
                else:
                    logging.warn(f'No pre-ring (muted)')
                    self.last_called_timing = timing

    def instant_ring(self, duration: float, sound = 0):
        duration = duration if duration <= configuration.rings.maximum else configuration.rings.maximum

        try:
            logging.warn(f'Started ring for {duration} seconds')
            ring_callbacks.ring(sound, duration)

            logging.warn(f'Stopped ring')
        
        except Exception as e:
            logging.critical('Unable to ring manually. The exception is below')
            logging.exception(e)

            try:
                ring_callbacks.stop_ring()
            except: os.system('reboot')
