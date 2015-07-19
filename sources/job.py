import os
import time
import threading

import requests
from requests.auth import HTTPBasicAuth
import paramiko

import logger

LOGGER = logger.get_logger(__name__)
URL = 'http://localhost:5000/wsexec/'
USERNAME = os.getenv('WSEXEC_USER')
PASSWORD = os.getenv('WSEXEC_PASS')

class myJob (threading.Thread):

    def __init__(self, job_id):
        threading.Thread.__init__(self)
        self.id = job_id

    def run(self):
        task = get_task(self.id)
        instance = get_instance(task['instance'])
        LOGGER.info("run task id %s" % str(self.id))

        try:
            rc, state, stdout, stderr = exec_task(task, instance)
        except Exception as e:
            ts = time.time()
            data = {"end": int(ts), "rc": 8000, "stdout": '', "stderr": "execution error", "state": "ABORT"}
            update_task(self.id, data)
            LOGGER.warning("exec_task error : %s %s" % (e.message, e.args))
        else:
            ts = time.time()
            data = {"end": int(ts), "rc": rc, "stdout": stdout, "stderr": stderr, "state": state}
            update_task(self.id, data)
            LOGGER.info("end task id %s" % str(self.id))

def get_task(id):
    try:
        r = requests.get(URL + "tasks/%s" % str(id), auth=HTTPBasicAuth(USERNAME, PASSWORD))
    except Exception as e:
        LOGGER.error("get task error : %s %s" % (e.message, e.args))
        raise e
    else:
        return r.json()['task']

def get_instance(id):
    try:
        r = requests.get(URL + "instances/%s" % str(id), auth=HTTPBasicAuth(USERNAME, PASSWORD))
    except Exception as e:
        LOGGER.error("get instance error: %s %s" % (e.message, e.args))
        raise e
    else:
        return r.json()['instance']

def update_task(id, data):
    try:
        r = requests.put(URL + "tasks/%s" % str(id), json=data, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    except Exception as e:
        LOGGER.error("put instance error: %s %s" % (e.message, e.args))
        raise e
    else:
        return r.json()['task']

def exec_task(task, instance):
    host = instance['ip']
    cmd = task['script']
    user = task['user']
    ssh, stdout, stderr, rc = "", "", "", ""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user)
        LOGGER.info("Connected to %s" % host)
    except paramiko.AuthenticationException as e:
        LOGGER.warning("Authentication failed when connecting to %s : %s %s" % (host, e.message, e.args))
        raise e
    except Exception as e:
        LOGGER.warning("Could not SSH to %s, waiting for it to start : %s %s" % (host, e.message, e.args))
        raise e

    try:
        chan = ssh.get_transport().open_session()
        chan.exec_command(cmd)
    except Exception as e:
        LOGGER.warning("exec_command error %s : %s %s" % (cmd, e.message, e.args))
        return e
    else:
        rc = chan.recv_exit_status()
        if chan.recv_ready():
            stdout = chan.recv(1601024)
        if chan.recv_stderr_ready():
            stderr = chan.recv_stderr(1601024)
        state = 'DONE'
        return rc, state, stdout, stderr

if __name__ == '__main__':
    id_task = 2
    monJob1 = myJob(id_task)
    monJob1.start()
