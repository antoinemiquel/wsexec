import os
import sys
import getopt
import time

import requests
from requests.auth import HTTPBasicAuth

"""
Exemples :
python ws_exec.py -t localhost:5000 -i 127.0.0.1 -u antoine -c "ls -als"
"""

WSEXEC_USER = os.getenv('WSEXEC_USER')
WSEXEC_PASS = os.getenv('WSEXEC_PASS')

def get_ws(url, clef):
    r = requests.get(url + clef, auth=HTTPBasicAuth(WSEXEC_USER, WSEXEC_PASS))
    return r.json()

def post_ws(url, clef, data):
    r = requests.post(url + clef, json=data, auth=HTTPBasicAuth(WSEXEC_USER, WSEXEC_PASS))
    return r.json()

def usage():
    message = 'ws_exec.py [-s] -t <tenant> -i <instance> -u <user> -c <script>\n'
    message += '-s : use ssl request\n'
    message += '-t : ip or name of target tenant\n'
    message += '-i : ip or name of target instance in the tenant\n'
    message += '-u : username of execution\n'
    message += '-c : command to execute'
    return message

def get_url(ssl, tenant):
    if ssl:
        url = "https://%s/wsexec/" % tenant
    else:
        url = "http://%s/wsexec/" % tenant
    return url

def check_args(argv):
    ssl = False
    tenant = ''
    instance = ''
    user = ''
    command = ''
    try:
        opts, args = getopt.getopt(argv, "hst:i:u:c:", ["tenant=", "instance=", "user=", "command="])
    except getopt.GetoptError:
        print usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print usage()
            sys.exit()
        elif opt in ("-s", "--ssl"):
            ssl = True
        elif opt in ("-t", "--tenant"):
            tenant = arg
        elif opt in ("-i", "--instance"):
            instance = arg
        elif opt in ("-u", "--user"):
            user = arg
        elif opt in ("-c", "--command"):
            command = arg

    if tenant == '' or instance == '' or user == '' or command == '':
        print usage()
        sys.exit(2)

    return ssl, tenant, instance, user, command

def launch_cmd(ssl, tenant, instance, user, command):
    url = get_url(ssl, tenant)
    task_result = ''

    instances = get_ws(url, "instances")['instances']
    instance_id = filter(lambda t: t['ip'] == instance, instances)[0]['id']

    loop = True
    data = {"name": "id_cmd", "tag": "unittest", "instance": instance_id, "script": command, "user": user}
    id_task = post_ws(url, "tasks", data)['task']['id']
    while loop:
        task = get_ws(url, "tasks/" + str(id_task))['task']
        if task['state'] == "DONE":
            task_result = task
            loop = False
        else:
            time.sleep(0.5)
    rc = task_result['rc']
    stdout = task_result['stdout']
    stderr = task_result['stderr']

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    sys.exit(rc)

if __name__ == "__main__":
    ssl, tenant, instance, user, command = check_args(sys.argv[1:])
    # print 'Tenant is "%s"' % tenant
    # print 'Instance is "%s"' % instance
    # print 'User is "%s"' % user
    # print 'Command is "%s"' % command

    launch_cmd(ssl, tenant, instance, user, command)
