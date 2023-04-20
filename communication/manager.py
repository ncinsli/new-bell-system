import requests
from datetime import datetime, timedelta

class NetManager:
    def __init__(self, host, password, device_id = None, self.token = None):
        self.host = host
        self.password = password
        self.token = token
        self.device_id = device_id
    
    def register():
        r = requests.post(self.host + "/api/devices/register", json = {"password": password})
        if r.status_code != 200:
            return r.status_code, r.text
        else:
            data = r.json()
            if "id" in data:
                self.device_id = int(data["id"])
                return r.status_code, data["id"]

    def wait_for_registration():
        data = None
        while True:
            r = requests.post(self.host + "/api/devices/wait_for_registration", json={"id": self.device_id}, timeout=120)
            if r.status_code == 200 and "token" in r.json():
                return r.json()
