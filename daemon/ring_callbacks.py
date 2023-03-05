import os
from telebot import *
import datetime
from pydub import AudioSegment, playback
import logging 
import configuration

port = configuration.port
sounds = {}

def init():
    logging.getLogger().warning(f'Initializing: echo {port} > /sys/class/gpio/export | echo out > /sys/class/gpio/gpio{port}/direction')

    os.system(f'echo {port} > /sys/class/gpio/export')
    os.system(f'echo out > /sys/class/gpio/gpio{port}/direction')

    for file in os.listdir('sounds'):
        path = os.path.abspath(f'sounds/{file}')
        load_sound(path)

def load_sound(sound_path: str):
    sound = AudioSegment.from_file(sound_path, sound_path[-3::])

    open_index = sound_path.index('[')
    close_index = sound_path.index(']')
    sounds[int(sound_path[open_index + 1 : close_index])] = sound

    print(sounds)

def start_ring(sound_index: int):
    os.system(f'echo 1 > /sys/class/gpio/gpio{port}/value')
    playback.play(sounds[sound_index])

def start_pre_ring(sound_index: int):
    os.system(f'echo 1 > /sys/class/gpio/gpio{port}/value')

def stop_ring():
    os.system(f'echo 0 > /sys/class/gpio/gpio{port}/value')
