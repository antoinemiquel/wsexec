__author__ = 'antoine'

import threading
import time
import requests
from requests.auth import HTTPBasicAuth
import paramiko
import os
import logger

LOGGER = logger.get_logger(__name__)
url = 'http://localhost:5000/wsexec/'
username = os.getenv('WSEXEC_USER')
password = os.getenv('WSEXEC_PASS')

class myJob (threading.Thread):

    def __init__(self, job_id):
        threading.Thread.__init__(self)
        self.id = job_id

    def run(self):
        task = get_task(self.id)
        instance = get_instance(task['instance'])
        LOGGER.info("run task id %s" % str(self.id))

        rc, state, stdout, stderr = exec_task(task, instance)

        ts = time.time()
        data = {"end": int(ts), "rc": rc, "stdout": stdout, "stderr": stderr, "state": state}
        update_task(self.id, data)
        LOGGER.info("end task id %s" % str(self.id))

def get_task(id):
    try:
        r = requests.get(url + "tasks/" + str(id), auth=HTTPBasicAuth(username, password))
    except:
        LOGGER.error("get task error")
    else:
        return r.json()['task']

def get_instance(id):
    try:
        r = requests.get(url + "instances/" + str(id), auth=HTTPBasicAuth(username, password))
    except:
        LOGGER.error("get instance error")
    else:
        return r.json()['instance']

def update_task(id, data):
    try:
        r = requests.put(url + "tasks/" + str(id), json=data, auth=HTTPBasicAuth(username, password))
    except:
        LOGGER.error("put instance error")
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
    except paramiko.AuthenticationException:
        LOGGER.info("Authentication failed when connecting to %s" % host)
    except:
        LOGGER.info("Could not SSH to %s, waiting for it to start" % host)

    try:
        chan = ssh.get_transport().open_session()
        chan.exec_command(cmd)
    except:
        LOGGER.info("exec_command error : %s" % cmd)
    else:
        rc = chan.recv_exit_status()
        if chan.recv_ready():
            stdout = chan.recv(1601024)
        if chan.recv_stderr_ready():
            stderr = chan.recv_stderr(1601024)
        stdout = stdout
        stderr = stderr
        state = 'DONE'
        return rc, state, stdout, stderr

if __name__ == '__main__':
    id_task = 2
    monJob1 = myJob(id_task)
    monJob1.start()
