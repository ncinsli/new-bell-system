import os
import toml
from datetime import datetime

class RingstableNamesConfiguration:
    main : str = 'bells'
    overrided : str = 'bell_overrides'
    admin : str = 'admin'
    sounds : str = 'sounds'

class PrivilegeConfiguration:
    owners : list = ['newbell_admin',]
    receivers : set = set(["1134602783",])

class RingTimingConfiguration:
    maximum : int = 5
    preparatory : int = 1 
    interval : int = 2
    main : int = 3
    first_preparatory_enabled : bool = True
    preparatory_enabled : bool = True
    default : int = 0

class DisplayConfiguration:
    delay : int = 3

class DaemonConfiguration:
    delay : int = 1
    port : int = 10 # 227

class Configuration:
    db : RingstableNamesConfiguration = RingstableNamesConfiguration()
    privileges : PrivilegeConfiguration = PrivilegeConfiguration()
    rings: RingTimingConfiguration = RingTimingConfiguration()

    display : DisplayConfiguration = DisplayConfiguration()
    daemon : DaemonConfiguration = DaemonConfiguration()
    status = f'Последний запуск: {datetime.now().strftime("%d.%m.%Y %H:%M")}'

    def __init__(self, parsed: dict = {}):
        
        if parsed == {}: return 

        status = 'Пусто'
        default = 0
        self.daemon.port = parsed['Out']['port']
        self.privileges.owners = parsed['Privileges']['owners']
        self.privileges.receivers = set(parsed['Privileges']['receivers'])

        self.db.main = parsed['Database']['name']
        self.db.overrided = parsed['Database']['override_name']
        self.db.admin = parsed['Database']['admin']
        # sounds_table_name = parsed['Database']['sounds']

        self.rings.main = parsed['Rings']['length']
        self.rings.maximum = parsed['Rings']['maxlength']
        self.rings.preparatory = parsed['Rings']['preparatory_length']
        self.rings.interval = parsed['Rings']['interval']
        self.rings.first_preparatory_enabled = parsed['Rings']['is_first_preparatory_enabled']
        self.rings.preparatory_enabled = parsed['Rings']['are_all_preparatory_enabled']
        self.rings.default = parsed['Rings']['default']

        self.display.delay = parsed['Display']['delay']
        self.daemon.delay = parsed['Daemon']['delay']

        self.status = parsed['Misc']['status']

    def to_dict(self) -> dict:
        parsed = {'Out' : dict(), 'Database' : dict(), 'Rings' : dict(), 'Privileges' : dict(), 'Display' : dict(), 'Daemon' : dict(), 'Misc' : dict()}
    
        parsed['Out']['port'] = self.daemon.port 
        parsed['Privileges']['owners'] = self.privileges.owners
        parsed['Privileges']['receivers'] = set(self.privileges.receivers)

        parsed['Database']['name'] = self.db.main 
        parsed['Database']['override_name'] = self.db.overrided
        parsed['Database']['admin'] = self.db.admin 
        # sounds_table_name = parsed['Database']['sounds']

        parsed['Rings']['length'] = self.rings.main 
        parsed['Rings']['maxlength'] = self.rings.maximum
        parsed['Rings']['preparatory_length'] = self.rings.preparatory
        parsed['Rings']['interval'] = self.rings.interval 
        parsed['Rings']['is_first_preparatory_enabled'] = self.rings.first_preparatory_enabled 
        parsed['Rings']['are_all_preparatory_enabled'] = self.rings.preparatory_enabled 
        parsed['Rings']['default'] = self.rings.default

        parsed['Display']['delay'] = self.display.delay
        parsed['Daemon']['delay'] = self.daemon.delay

        parsed['Misc']['status'] = self.status

        return parsed

    def save(self):
        with open('configuration.toml', 'w', encoding='utf-8') as f:
            toml.dump(configuration.to_dict(), f)


if os.path.exists('configuration.toml'):
    configuration = Configuration(toml.load('configuration.toml'))
else:
    configuration = Configuration()
    configuration.save()

def reset_configuration(cfg): # вызывается в middleware /set_Ringstable. В случае, если в Ringstable.json не были указаны эти данные.
    global interval, length, max_ring_duration, preparatory_ring_duration, first_pre_ring_enabled, all_pre_ring_enabled
    interval = cfg[0]
    length = cfg[1]
    lengthtion = cfg[2]
    preparatory_length = cfg[3]
    first_pre_ring_enabled = cfg[4]
    all_pre_ring_enabled = cfg[5]
    

def default_configuration():
    global interval, length, max_ring_duration, preparatory_ring_duration, first_pre_ring_enabled, all_pre_ring_enabled
    interval = 120
    length = 3
    lengthtion = 4
    preparatory_length = 1
    first_pre_ring_enabled = True
    all_pre_ring_enabled = True
