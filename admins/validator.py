import sqlite3
import admins.storage
from configurations import configuration

def check(message) -> bool:
    return admins.storage.contains(str(message.from_user.username).lower()) or admins.storage.contains(str(message.from_user.id))