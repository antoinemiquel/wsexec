__author__ = 'antoine'

import redis

def init_db(bdd_id):
    # __________________________________ data __________________________________

    tasks = [
        {
            'id': 1,
            'name': 'save_mongo',
            'tag': 'dump mongo',
            'start': 1436506743,
            'end': 1436506790,
            'instance': 200,
            'script': '/home/debian/mongo_save.sh',
            'user': 'debian',
            'stdout': 'NOK',
            'stderr': '',
            'rc': 1,
            'state': 'DONE'
        },
        {
            'id': 2,
            'name': 'save_mongo',
            'tag': 'dump mongo',
            'start': 1436506000,
            'end': 1436506090,
            'instance': 200,
            'script': '/home/debian/mongo_save.sh',
            'user': 'debian',
            'stdout': 'ok',
            'stderr': '',
            'rc': 0,
            'state': 'DONE'
        }
    ]

    instances = [
        {
            'id': 200,
            'ip': '127.0.0.1',
            'tag': 'local',
            'state': 'ACTIVE'
        }
    ]

    pool = redis.ConnectionPool(host='localhost', port=6379, db=bdd_id)
    r = redis.Redis(connection_pool=pool)

    r.flushdb()
    r.set("tasks", tasks)
    r.set("instances", instances)

# __________________________________ main __________________________________

if __name__ == '__main__':
    init_db(0)
