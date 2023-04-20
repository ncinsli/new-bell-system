import os
import copy
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
    auto : bool = False

class DisplayConfiguration:
    delay : int = 3
    port: int = 3

class DaemonConfiguration:
    delay : int = 1
    port : int = 10 # 227

class NetDeviceConfiguration:
    host: str = "185.246.64.64:5000"
    name: str = ""
    id: int = -1

class Configuration:
    db : RingstableNamesConfiguration = RingstableNamesConfiguration()
    privileges : PrivilegeConfiguration = PrivilegeConfiguration()
    rings: RingTimingConfiguration = RingTimingConfiguration()

    display : DisplayConfiguration = DisplayConfiguration()
    daemon : DaemonConfiguration = DaemonConfiguration()
    netdevice: NetDeviceConfiguration = NetDeviceConfiguration()
    cli_mode = True
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
        self.rings.auto = parsed['Rings']['auto']

        self.display.delay = parsed['Display']['delay']
        self.display.port = parsed['Display']['port']
        self.daemon.delay = parsed['Daemon']['delay']

        self.status = parsed['Misc']['status']
        self.cli_mode = parsed['Misc']['cli_mode']

        self.netdevice.host = parsed['NetDevice']['host']

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
        parsed['Rings']['auto'] = self.rings.auto

        parsed['Display']['delay'] = self.display.delay
        parsed['Display']['port'] = self.display.port
        parsed['Daemon']['delay'] = self.daemon.delay

        parsed['Misc']['status'] = self.status
        parsed['Misc']['cli_mode'] = self.cli_mode

        return parsed

    def save(self):
        with open('configuration.toml', 'w', encoding='utf-8') as f:
            toml.dump(configuration.to_dict(), f)
    def get_instance(self):
        return copy.deepcopy(self)
    def set(self, instance):
        self.daemon.port = instance.daemon.port
        self.privileges.owners = instance.privileges.owners
        self.privileges.receivers = instance.privileges.receivers
        
        self.db.main = instance.db.main
        self.db.overrided = instance.db.overrided
        self.db.admin = instance.db.admin

        self.rings.main = instance.rings.main
        self.rings.maximum = instance.rings.maximum
        self.rings.preparatory = instance.rings.preparatory
        self.rings.interval = instance.rings.interval
        self.rings.first_preparatory_enabled = instance.rings.first_preparatory_enabled
        self.rings.preparatory_enabled = instance.rings.preparatory_enabled
        self.rings.default = instance.rings.default

        self.display.delay = instance.display.delay
        self.display.port = instance.display.port
        self.daemon.delay = instance.daemon.delay

        self.status = instance.status

if os.path.exists('configuration.toml'):
    configuration = Configuration(toml.load('configuration.toml'))
else:
    configuration = Configuration()
    configuration.save()