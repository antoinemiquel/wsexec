__author__ = 'antoine'

import os
import wsexec
import unittest
import redis
import requests
from requests.auth import HTTPBasicAuth
import time
import logger

class WsexecTestCase(unittest.TestCase):

    def setUp(self):
        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.r = redis.Redis(connection_pool=pool)

        self.url = 'http://localhost:5000/wsexec/'
        self.username = os.getenv('WSEXEC_USER')
        self.password = os.getenv('WSEXEC_PASS')
        self.LOGGER = logger.get_logger(__name__)

    def tearDown(self):
        self.r.connection_pool.disconnect()

    def get_ws(self, clef):
        r = requests.get(self.url + clef, auth=HTTPBasicAuth(self.username, self.password))
        return r.json()

    def post_ws(self, clef, data):
        r = requests.post(self.url + clef, json=data, auth=HTTPBasicAuth(self.username, self.password))
        return r.json()

    def put_ws(self, clef, data):
        r = requests.put(self.url + clef, json=data, auth=HTTPBasicAuth(self.username, self.password))
        return r.json()

    def delete_ws(self, clef):
        r = requests.delete(self.url + clef, auth=HTTPBasicAuth(self.username, self.password))
        return r.json()

    def test_get_tasks(self):
        nb_ws = len(self.get_ws("tasks")['tasks'])
        nb_bdd = len(wsexec.get_json("tasks"))
        self.assertEqual(nb_ws, nb_bdd)

    def test_get_instances(self):
        nb_ws = len(self.get_ws("instances")['instances'])
        nb_bdd = len(wsexec.get_json("instances"))
        self.assertEqual(nb_ws, nb_bdd)

    def test_set_json(self):
        wsexec.set_json("test", "valeur_test")
        if wsexec.get_json("test") == "valeur_test":
            rc = 0
        else:
            rc = 1
        wsexec.init_db().delete("test")
        self.assertEqual(rc, 0)

    def test_create_task(self):
        nb_tasks_begin = len(self.get_ws("tasks")['tasks'])
        data = {"name": "id_cmd", "tag": "unittest", "instance": 200, "script": "id", "user": "antoine"}
        id_task = self.post_ws("tasks", data)['task']['id']
        while True:
            task = self.get_ws("tasks/" + str(id_task))['task']
            if task['state'] == "DONE":
                self.assertEqual(task['rc'], 0)
                break
            else:
                time.sleep(0.5)

        data = {"rc": 20}
        rc = self.put_ws("tasks/" + str(id_task), data)['task']['rc']
        self.assertEqual(data['rc'], rc)

        self.delete_ws("tasks/" + str(id_task))
        nb_tasks_end = len(self.get_ws("tasks")['tasks'])
        self.assertEqual(nb_tasks_begin, nb_tasks_end)

    def test_create_instances(self):
        nb_instances_begin = len(self.get_ws("instances")['instances'])
        data = {"ip": "127.0.0.1", "tag": "localhost", "state": "ACTIVE"}
        id_instance = self.post_ws("instances", data)['instance']['id']
        instance = self.get_ws("instances/" + str(id_instance))['instance']
        self.assertEqual(instance['ip'], data['ip'])

        data = {"ip": "127.0.0.2"}
        self.put_ws("instances/" + str(id_instance), data)
        ip = self.get_ws("instances/" + str(id_instance))['instance']['ip']
        self.assertEqual(data['ip'], ip)

        self.delete_ws("instances/" + str(instance['id']))
        nb_instances_end = len(self.get_ws("instances")['instances'])
        self.assertEqual(nb_instances_begin, nb_instances_end)

if __name__ == '__main__':
    unittest.main()
