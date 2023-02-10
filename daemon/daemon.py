try: import displaying.LCD_2004
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
import configuration
from datetime import datetime
import daemon.ring_callbacks as ring_callbacks

class Daemon(threading.Thread):
    today_timetable: list
    muted_rings: list
    order = 0
    last_called_timing: str = '00:00'
    next_called_timing: str = '00:00'
    gpio_mode = False
    debugger : telebot.TeleBot
    day: int

    def __init__(self, table, muted):
        super().__init__()

        log_filename = os.path.join('logs', f'{datetime.now().strftime("%a %d %b %Y %H;%M;%S")}.log')
        
        self.daemon = True
        self.update(table, muted)
        self.day = datetime.now().day
        
        if (os.system(f'echo 1 > /sys/class/gpio10/value && echo 0 > /sys/class/gpio{configuration.port}/value') == 0):
            self.gpio_mode = True

        logging.info(f'GPIO_MODE: {self.gpio_mode}')
        
        ring_callbacks.init()
        self.update_ring_order()

        try: displaying.LCD_2004.initial_output(self.today_timetable)
        except: print("[GPIO] .initial_output")

    def update_ring_order(self):
        self.order = utils.nearest_forward_ring_index(self.today_timetable)
        logging.info(f'Updated ring order to: {self.order}')

    def update(self, new_timetable, new_muted):
        self.today_timetable, self.muted_rings = new_timetable, new_muted # Обращаться к sqlite из другого потока нельзя
        self.today_timetable = list(map(lambda e: e.zfill(5), self.today_timetable))
        
        try: displaying.LCD_2004.update(self.today_timetable, self.order, self.next_called_timing)
        except: print("[GPIO] .update")
        timetable_str = str(self.today_timetable).replace("'", "")
        logging.info(f'Updated timetable: {timetable_str}')
        logging.info(f'Updated muted list: {str(self.muted_rings)}')

    def run(self):
        while True:
            time.sleep(1)
            timing = str(datetime.now().time())[:5]
            timing_forward = timetable.utils.sum_times(timing, configuration.pre_ring_delta)

            if (timing == '00:00' and datetime.now().day != self.day): 
                self.update(*timetable.getting.get_time(datetime.now()))
                self.day = datetime.now().day

            if (timing in self.today_timetable and timing != self.last_called_timing):
                self.order += 1

                self.order = self.today_timetable.index(str(datetime.now().time())[:5])
                logging.info(f'It is an event: order is now {self.order}')

                if self.muted_rings[self.order] == 0:
                    logging.warn(f'Started ring for {configuration.ring_duration} seconds')
                    ring_callbacks.start_ring()
                    time.sleep(configuration.ring_duration)
                    ring_callbacks.stop_ring()
                    logging.warn(f'Stopped ring')

                    self.last_called_timing = timing

                    try:
                        for id in configuration.debug_info_receivers:
                            self.debugger.send_message(id, '🛎️  Звонок по расписанию успешно подан')
                    except: logging.error("Unable to notify debug info receivers about the ring")

                else:
                    logging.warn(f'No ring (muted)')
                    self.last_called_timing = timing
                    try:
                        for id in configuration.debug_info_receivers:
                            self.debugger.send_message(id, '🚫 Звонок по расписанию заглушен и не подан')
                    except: logging.error("Unable to notify debug info receivers about the muted ring")

                tempIdx = self.today_timetable.index(timing)
                if tempIdx != len(self.today_timetable)-1:
                    self.next_called_timing = self.today_timetable[tempIdx+1]

                    try: displaying.LCD_2004.next(self.today_timetable, tempIdx+1)
                    except: print("[GPIO] .next")

                else:
                    self.next_called_timing = "-1" # no more rings for today
                    
                    try: displaying.LCD_2004.no_more_rings()
                    except: print("[GPIO] .no_more_rings")

                    logging.warn(f'No more rings')
                
                    try:
                        for id in configuration.debug_info_receivers:
                            self.debugger.send_message(id, '⏰ Сегодня больше нет звонков')
                    except: logging.error("Unable to notify debug info receivers about the ending of all rings")


                if self.order + 1 <= len(self.today_timetable) - 1:
                    if self.today_timetable[self.order+1] == self.today_timetable[self.order]:
                        try: displaying.LCD_2004.next(self.today_timetable, self.order+1)
                        except: print("[GPIO] .next")

            if (timing_forward in self.today_timetable and timing != self.last_called_timing):
                self.order = self.today_timetable.index(timing_forward)

                if self.order % 2 != 0: continue

                if self.muted_rings[self.order] == 0:
                    logging.warn(f'Started pre-ring for {configuration.pre_ring_duration} seconds')

                    ring_callbacks.start_pre_ring()
                    time.sleep(configuration.pre_ring_duration)
                    ring_callbacks.stop_ring()
                    
                    logging.warn(f'Stopped pre-ring')

                    try:
                        for id in configuration.debug_info_receivers:
                            self.debugger.send_message(id, '🧨  Предзвонок по расписанию успешно подан')
                    except: logging.error("Unable to notify debug info receivers about pre-ring")

                    self.last_called_timing = timing
                else:
                    logging.warn(f'No pre-ring (muted)')
                    self.last_called_timing = timing

    def instant_ring(self, duration: float):
        try:
            logging.warn(f'Started ring for {duration if duration <= configuration.max_ring_duration else configuration.max_ring_duration} seconds')
            ring_callbacks.start_ring()
            time.sleep(duration if duration <= configuration.max_ring_duration else configuration.max_ring_duration)
            ring_callbacks.stop_ring()

            logging.warn(f'Stopped ring')
        except:
            logging.critical('Unable to ring manually')
        
            try:
                ring_callbacks.stop_ring()
            except: os.system('reboot')