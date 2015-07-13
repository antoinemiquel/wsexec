__author__ = 'antoine'

import os
import wsexec
import unittest
import redis
import requests
from requests.auth import HTTPBasicAuth

class WsexecTestCase(unittest.TestCase):

    def setUp(self):
        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.r = redis.Redis(connection_pool=pool)
        wsexec.app.config['TESTING'] = True
        self.app = wsexec.app.test_client()

        self.url = 'http://localhost:5000/wsexec/'
        self.username = os.getenv('WSEXEC_USER')
        self.password = os.getenv('WSEXEC_PASS')

    def tearDown(self):
        pass

    def get_ws(self, clef):
        r = requests.get(self.url + clef, auth=HTTPBasicAuth(self.username, self.password))
        return r.json()[clef]

    def test_get_tasks(self):
        nb_ws = len(self.get_ws("tasks"))
        nb_bdd = len(wsexec.get_json("tasks"))
        self.assertEqual(nb_ws, nb_bdd)

    def test_get_instances(self):
        nb_ws = len(self.get_ws("instances"))
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


if __name__ == '__main__':
    unittest.main()