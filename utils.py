import configuration
import subprocess
import os
import logging

def get_cpu_temp():
    try:
        tempfile = open('/sys/class/thermal/thermal_zone0/temp')
        cpu_temp = tempfile.read()
        tempfile.close()
        return float(cpu_temp) / 1000
    except:
        logging.getLogger().error("Failed to get CPU temp. Make sure you're running this on linux-based machine")
        return '2.000.000'
def get_uptime():
    try:
        return str(subprocess.check_output('uptime -p'.split()))
    except: 
        logging.getLogger().error("Failed to get uptime. Make sure you're running this on linux-based machine")
        return '1 секунда'

def get_exception_handler(bot):
    
    def exception_handler(exc_type, exc_value, traceback):
        logging.exception(str(exc_type) + ' ' + str(exc_value) + ' ' + str(traceback))

        for id in configuration.debug_info_receivers: 
            bot.send_message(id, '🌪  Ошибка системы:\n' + str(exc_type) + ' ' + str(exc_value) + ' ' + str(traceback))

    return exception_handler    
