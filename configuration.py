import sqlite3

port = 227
connection = sqlite3.connect('database.db', check_same_thread=False)
owners = ['newbell_admin']
debug_info_receivers = set(['1134602783'])

time_table_name = 'bells'
overrided_time_table_name = 'bell_overrides'
admin_table_name = 'admins'
pre_ring_delta = 120

ring_duration = 3
max_ring_duration = 4
pre_ring_duration = 1
status = 'Пусто'

default_ring = 0
