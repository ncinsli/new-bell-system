import os
from telebot import *
import datetime
import logging 
import configuration

port = configuration.port

def init():
    logging.getLogger().warning(f'Initializing: echo {port} > /sys/class/gpio/export | echo out > /sys/class/gpio/gpio{port}/direction')

    os.system(f'echo {port} > /sys/class/gpio/export')
    os.system(f'echo out > /sys/class/gpio/gpio{port}/direction')

def start_ring():
    os.system(f'echo 1 > /sys/class/gpio/gpio{port}/value')

def start_pre_ring():
    os.system(f'echo 1 > /sys/class/gpio/gpio{port}/value')

def stop_ring():
    os.system(f'echo 0 > /sys/class/gpio/gpio{port}/value')
