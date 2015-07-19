import os
import unittest
from base64 import b64encode

import redis
import json

import logger
import wsexec
import init_redis


def simple_task_launch(task):
    return task

class WsexecTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pool = redis.ConnectionPool(host='localhost', port=6379, db=1)
        cls.r = redis.Redis(connection_pool=pool)

        wsexec.application.config['TESTING'] = True
        wsexec.BDD_ID = 1
        cls.app = wsexec.application.test_client()

        cls.url = 'http://localhost:5000/wsexec/'
        cls.username = os.getenv('WSEXEC_USER')
        cls.password = os.getenv('WSEXEC_PASS')
        cls.headers = {'Authorization': 'Basic ' + b64encode("{0}:{1}".format(cls.username, cls.password))}
        cls.LOGGER = logger.get_logger(__name__)

    @classmethod
    def tearDownClass(cls):
        cls.r.connection_pool.disconnect()

    def setUp(self):
        init_redis.init_db(1)

    def test_get_tasks(self):
        rv = json.loads(self.app.get('/wsexec/tasks', headers=self.headers).data)["tasks"]

        # nombre de taches
        self.assertEqual(len(rv), 2)

        # id taches
        self.assertEqual(rv[0]['id'], 1)
        self.assertEqual(rv[1]['id'], 2)

    def test_get_task(self):
        rv = json.loads(self.app.get('/wsexec/tasks/1', headers=self.headers).data)["task"]

        # id tache
        self.assertEqual(rv['id'], 1)
        self.assertEqual(rv['name'], 'save_mongo')
        self.assertEqual(rv['tag'], 'dump mongo')
        self.assertEqual(rv['start'], 1436506743)
        self.assertEqual(rv['end'], 1436506790)
        self.assertEqual(rv['instance'], 200)
        self.assertEqual(rv['script'], '/home/debian/mongo_save.sh')
        self.assertEqual(rv['user'], 'debian')
        self.assertEqual(rv['stdout'], 'NOK')
        self.assertEqual(rv['stderr'], '')
        self.assertEqual(rv['rc'], 1)
        self.assertEqual(rv['state'], 'DONE')

    def test_get_instances(self):
        rv = json.loads(self.app.get('/wsexec/instances', headers=self.headers).data)["instances"]

        # nombre d'instance
        self.assertEqual(len(rv), 1)

        # id instance
        self.assertEqual(rv[0]['id'], 200)

    def test_get_instance(self):
        rv = json.loads(self.app.get('/wsexec/instances/200', headers=self.headers).data)["instance"]

        # id instance
        self.assertEqual(rv['id'], 200)
        self.assertEqual(rv['ip'], '127.0.0.1')
        self.assertEqual(rv['tag'], 'local')
        self.assertEqual(rv['state'], 'ACTIVE')


if __name__ == '__main__':
    unittest.main()
