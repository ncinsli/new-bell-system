import sqlite3

port = 227
connection = sqlite3.connect('database.db', check_same_thread=False)
owners = ['newbell_admin']
debug_info_receivers = set(['1134602783'])

time_table_name = 'bells'
overrided_time_table_name = 'bell_overrides'
admin_table_name = 'admins'
sounds_table_name = 'sounds'

pre_ring_delta = 120
ring_duration = 3
max_ring_duration = 4
pre_ring_duration = 1
first_pre_ring_enabled = True
all_pre_rings_enabled = True 

display_delay_time = 3
daemon_delay_time = 1


status = 'Пусто'
default_ring = 0

def reset_configuration(cfg): # вызывается в middleware /set_timetable. В случае, если в timetable.json не были указаны эти данные.
    global pre_ring_delta, ring_duration, max_ring_duration, pre_ring_duration, first_pre_ring_enabled, all_pre_rings_enabled
    pre_ring_delta = cfg[0]
    ring_duration = cfg[1]
    max_ring_duration = cfg[2]
    pre_ring_duration = cfg[3]
    first_pre_ring_enabled = cfg[4]
    all_pre_rings_enabled = cfg[5]

def default_configuration():
    global pre_ring_delta, ring_duration, max_ring_duration, pre_ring_duration, first_pre_ring_enabled, all_pre_rings_enabled
    pre_ring_delta = 120
    ring_duration = 3
    max_ring_duration = 4
    pre_ring_duration = 1
    first_pre_ring_enabled = True
    all_pre_rings_enabled = True