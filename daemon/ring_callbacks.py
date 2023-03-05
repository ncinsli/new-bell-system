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
    try:
        sound = AudioSegment.from_file(sound_path, sound_path[-3::])
        sounds[sound_path.rindex('/') + 1] = sound
    except:
        logger.critical("Failed to load sound on path " + sound_path)

def ring(sound: string, duration = configuration.ring_duration):
    os.system(f'echo 1 > /sys/class/gpio/gpio{port}/value')
    time.sleep(0.1) # Для передачи системе оповещения тока, который скажет ей включить линейный вход, нужно время

    try:
        playback.play(sounds[sound][0:duration * 1000])
        stop_ring()

    except Exception as e:
        logging.getLogger().critical("Unable to start sound ring")
        time.sleep(duration - 0.1)
        stop_ring()

def stop_ring():
    os.system(f'echo 0 > /sys/class/gpio/gpio{port}/value')
