import requests
from datetime import datetime, timedelta

import threading
import hashlib
import time
import os, subprocess

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
            try:
                if self.work:
                    stats = self.get_system_stats()
                    r = requests.post(self.host + "/api/devices/refresh", headers={"Authorization": "Bearer " + self.token}, json = stats, timeout=30)
                    data = r.json()

                    if r.status_code == 200 and "data" in data:
                        self.try_request(r.json())
                    
                if self.wait:
                    r = requests.post(self.host + "/api/devices/wait_for_registration", json={"id": self.device_id}, timeout=20)
                    if r.status_code == 200 and "token" in r.json():
                        data = r.json()
                        self.token = data["token"]
                        self.name = data["name"]
                        self.wait = False
                        self.work = True
            except Exception as e:
                print(e)
                

    def register(self, id):
        if id == -1:
            r = requests.post(self.host + "/api/devices/register", json = {"password": self.password})
            if r.status_code != 200:
                return r.status_code, r.text
            else:
                data = r.json()
                if "id" in data:
                    self.device_id = int(data["id"])
                    return 0, data
        else:
            self.device_id = id
            return 0, {"id": id}

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
        print('[NETMANAGER] parsing request')
        response = {"data": []}

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
            
            if "type" not in req["content"]:
                continue
 
            content = req["content"]

            req_response = "done"

            if content["type"] == "UPDATE":
                os.system("python3 /root/update.py")
                response["data"].append({"id": req["id"], "response": "UPDATING"})
                return self.response(response)
            
            if content["type"] == "EXECUTE":
                if "prompt" in content:
                    try:
                        req_response = subprocess.check_output(content["prompt"].split())
                    except:
                        req_response = "Execution error"

            if content["type"] == "LOCK":
                print("TODO: think about what is softlock for us")
            if content["type"] == "UNLOCK":
                print("TODO: think about what is softlock for us")
            
            response["data"].append({"id": req["id"], "response": str(req_response), "type": "response"})

        return self.response(response)

    def response(self, data):
        r = requests.post(self.host + "/api/devices/response", headers={"Authorization": "Bearer " + self.token}, json = data)
        return r.status_code, r.text
