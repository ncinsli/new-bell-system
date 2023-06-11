import requests
from datetime import datetime, timedelta

import threading
import hashlib
import time
import os, subprocess, signal, psutil
import socketio

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
        self.daemon = True # threading
        self.sio = None

        self.processes =  {}
    
    def run(self):
        data = None
        while True:
            try:
                if self.work:
                    break
                    
                if self.wait:
                    r = requests.post(self.host + "/api/devices/wait_for_registration", json={"id": self.device_id}, timeout=120)
                    if r.status_code == 200 and "token" in r.json():
                        data = r.json()
                        self.token = data["token"]
                        self.name = data["name"]
                        self.wait = False
                        self.work = True
            except Exception as e:
                print(e)
        
        if self.work:
            sio = socketio.Client()
            self.sio = sio
            @sio.event(namespace="/refreshing")
            def interrupt(data):
                if self.device_id in data["ids"]:
                    if data["execution_id"] in self.processes.keys():
                        self.kill_process(data["execution_id"])

            @sio.event(namespace="/refreshing")
            def request(data):
                threading.Thread(target=self.try_request, args=(data, sio, )).start()

            @sio.event(namespace="/refreshing")
            def connect():
                print("[NETMANAGER] connecting established")
                print("[NETMANAGER] syncing processes")
                self.sync_processes()
                self.work = True
                refreshing_task_thread = sio.start_background_task(refreshing_task)

            @sio.event(namespace="/refreshing")
            def disconnect():
                print("[NETMANAGER] disonnected")
                self.work = False
                threading.Thread(target=self.retry_login, args=(self.device_id, "Zvonki2023", ), daemon=True).start()
                while not self.work:
                    time.sleep(0.1)
                    pass
                time.sleep(3)
                self.work = False
                reconnect_task_thread = sio.start_background_task(reconnection_task)

            def disconnection_task(exit_st):
                while not exit_st[0]:
                    pass
                sio.disconnect()

            def refreshing_task():
                if self.work:
                    print("[NETMANAGER] refreshing task started")
                while self.work:
                    stats = self.get_system_stats()
                    stats["token"] = self.token
                    try:
                        sio.emit("refresh", stats, namespace="/refreshing")
                    except:
                        if not self.work:
                            break
                    time.sleep(5)

            def reconnection_task():
                while not self.work:
                    try:
                        print("[NETMANAGER] reconnecting")
                        sio.connect(self.host, headers={"Authorization": "Bearer " + self.token}, namespaces=["/refreshing"], wait_timeout = 10)
                        self.work = True
                        sio.wait()
                        break
                    except:
                        pass
                    time.sleep(5)
            
            while self.work:
                try:
                    sio.connect(self.host, headers={"Authorization": "Bearer " + self.token}, namespaces=["/refreshing"], wait_timeout = 10)
                    refreshing_task_thread = sio.start_background_task(refreshing_task)
                    sio.wait()
                    break
                except:
                    pass            
            

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

    def retry_login(self, id, password):
        while True:
            time.sleep(5)
            print("[NETMANAGER] trying to auth")
            try:
                ret, text = self.login(id, password)
                if ret == 0:
                    print("[NETMANAGER] Successfull auth!")
                    break
            except:
                pass
        return

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
    
    def try_request(self, data, sio):
        print('[NETMANAGER] parsing request')

        if data["ids"] != "all":
            if self.device_id not in data["ids"]:
                return

        if data["type"] == "execute":
            print(f"[NETMANAGER] starting process. execution_id: {data['content']['execution_id']}")
            if data["content"]["failsafe_mode"]:
                threading.Thread(target=self.killer, args=(data["content"]["failsafe_timeout"], data["content"]["execution_id"])).start()
            self.processes[data["content"]["execution_id"]] = subprocess.Popen(data["content"]["cmd"], stdout=subprocess.PIPE, shell=True)
            out, err = self.processes[data["content"]["execution_id"]].communicate()
            if out != None: 
                out = out.decode("utf-8")
            else:
                out = ""
            if err != None:
                err = err.decode("utf-8")
            else:
                err = ""

            sio.emit("device_response", {"type": "device_response", "response": out, "execution_id": data["content"]["execution_id"], "errors": err, "token": self.token}, namespace="/refreshing")
            try: del self.processes[data["content"]["execution_id"]]
            except: pass
        elif data["type"] == "interrupt":
            if data["execution_id"] == "all":
                keys = list(self.processes.keys()).copy()
                for p in keys:
                    try: self.kill_process(p)
                    except: pass
                self.processes = {}

            else:
                if data["execution_id"] not in self.processes.keys():
                    #sio.emit("device_response", {"type": "device_response", "response": "", "execution_id": data["execution_id"], "errors": "Process not started", "token": self.token}, namespace="/refreshing")
                    return
                
                self.kill_process(data["execution_id"])
                try: del self.processes[data["execution_id"]]
                except: pass

    def response(self, data):
        r = requests.post(self.host + "/api/devices/response", headers={"Authorization": "Bearer " + self.token}, json = data)
        return r.status_code, r.text

    def killer(self, timeout, execution_id):
        time.sleep(float(timeout))
        self.kill_process(execution_id)

    def kill_process(self, execution_id):
        try:
            if os.name == 'nt':
                subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=self.processes[execution_id].pid))
            else:
                kill_child_processes(self.processes[execution_id].pid)
        except:
            try: print(f"[NETMANAGER] couldn't kill process. execution_id: {execution_id}. pid: {self.processes[execution_id].pid}")
            except: print("[NETMANAGER] couldn't kill process. process was already killed")

    def sync_processes(self):
        r = requests.post(self.host + "/api/devices/sync_processes", headers={"Authorization": "Bearer " + self.token})    
        processes = r.json()["processes"]
        for p in processes:
            threading.Thread(target=self._process_thread, args=(p, ), daemon=True).start()
    
    def _process_thread(self, process):
        print(f"[NETMANAGER] starting process. execution_id: {process['execution_id']}")
        if process["failsafe_mode"]:
            threading.Thread(target=self.killer, args=(process["failsafe_timeout"], process["execution_id"])).start()
        self.processes[process["execution_id"]] = subprocess.Popen(process["cmd"], stdout=subprocess.PIPE, shell=True)
        out, err = self.processes[process["execution_id"]].communicate()
        if out != None: 
            out = out.decode("utf-8")
        else:
            out = ""
        if err != None:
            err = err.decode("utf-8")
        else:
            err = ""

        self.sio.emit("device_response", {"type": "device_response", "response": out, "execution_id": process["execution_id"], "errors": err, "token": self.token}, namespace="/refreshing")
        try: del self.processes[process["execution_id"]]
        except: pass


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
      parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
      return
    children = parent.children(recursive=True)
    for process in children:
      process.send_signal(sig)