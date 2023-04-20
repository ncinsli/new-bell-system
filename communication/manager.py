import requests
from datetime import datetime, timedelta

import threading
import hashlib
import time
import os

class NetManager(threading.Thread):
    def __init__(self, host, password, func, device_id = None, token = None):
        super().__init__()
        self.host = host
        self.get_system_stats = func
        self.password = hashlib.md5(password.encode('utf8')).hexdigest()
        self.token = token
        self.device_id = device_id
        self.work = False
        self.wait = False
        self.readids = []
    
    def run(self):
        data = None
        while True:
            if self.work:
                stats = self.get_system_stats()
                stats["id"] = self.device_id
                try:
                    r = requests.post(self.host + "/api/devices/refresh", headers={"Authorization": "Bearer " + self.token}, json = stats, timeout=10)
                    data = r.json()

                    if r.status_code == 200 and "data" in data:
                        t = threading.Thread(target=self.try_request, args=(r.json(), ))
                        t.start()
                except:
                    pass
                

            if self.wait:
                r = requests.post(self.host + "/api/devices/wait_for_registration", json={"id": self.device_id}, timeout=120)
                if r.status_code == 200 and "token" in r.json():
                    data = r.json()
                    self.token = data["token"]
                    self.name = data["name"]
                    self.wait = False
                    self.work = True

    def register(self):
        r = requests.post(self.host + "/api/devices/register", json = {"password": self.password})
        if r.status_code != 200:
            return r.status_code, r.text
        else:
            data = r.json()
            if "id" in data:
                self.device_id = int(data["id"])
                return 0, data

    def wait_for_registration(self):
        self.wait = True
    
    def get_wait_state(self):
        return self.wait

    def get_name(self):
        return self.name

    def login(self, id, password):
        self.device_id = id
        self.password = password
        r = requests.post(self.host + "/api/login", json = {"device_id": self.device_id, "password": hashlib.md5(password.encode('utf8')).hexdigest()}, timeout=30)
        if r.status_code != 200:
            return r.status_code, r.text
        else:
            data = r.json()
            if "token" in data:
                self.token = data["token"]
                self.work = True
                return 0, r.text
    
    def try_request(self, data):
        # just to check(github)
        for req in data["data"]:
            if "id" in req:
                if len(self.readids) > 0:
                    if req["id"] in self.readids:
                        continue
                else:
                    self.readids = [req["id"]]
            else:
                continue
            
            self.readids.append(req["id"])


            if "content" not in req:
                continue
            
            if "type" in req["content"]:
                if "ids" in req["content"]:
                    if self.device_id not in req["content"]:
                        continue
            else:
                continue
 
            content = req["content"]

            if content["type"] == "UPDATE":
                os.system("python3 /root/update.py")
            
            if content["type"] == "EXECUTE":
                if "prompt" in content:
                    os.system(content["prompt"])

            if content["type"] == "LOCK":
                print("TODO: think about what is softlock for us")
            if content["type"] == "UNLOCK":
                print("TODO: think about what is softlock for us")