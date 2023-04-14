import threading
import sys

import json
import sys
import subprocess
from telebot import *
from datetime import datetime
from daemon.daemon import Daemon
from datetime import datetime, timedelta
from configurations import configuration
from daemon import ring_callbacks
import replies.format_tip, replies.results
import utils
import cli

from singletones import connection
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
import timetable.utils
from admins import *
from displaying import *


def socket():
    while True:
        try:
            command = input('Admin@Newbell $ ')
            if command != '':
                print(eval(command))
        except Exception as e: 
            print(e)

def push(command):
    eval(command)

command_listener = threading.Thread(target=socket)
command_listener.setDaemon(True)