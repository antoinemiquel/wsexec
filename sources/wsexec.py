__author__ = 'antoine'

from flask import Flask, jsonify, abort, request, make_response, url_for
from flask.ext.httpauth import HTTPBasicAuth
import job
import time
import os
import redis
import json

app = Flask(__name__, static_url_path="")
auth = HTTPBasicAuth()
wsexec_user = os.getenv('WSEXEC_USER')
wsexec_pass = os.getenv('WSEXEC_PASS')

def init_db():
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    return redis.Redis(connection_pool=pool)

def get_json(clef):
    conn = init_db()
    return json.loads(conn.get(clef).replace("'", "\""))

def set_json(clef, json_data):
    conn = init_db()
    conn.set(clef, json.dumps(json_data))

@auth.get_password
def get_password(username):
    if username == wsexec_user:
        return wsexec_pass
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

# __________________________________ tasks __________________________________

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
            new_task[field] = task[field]
        else:
            new_task[field] = task[field]
    return new_task

def task_request_check(request):
    if not request.json \
            or not 'name' in request.json \
            or not 'instance' in request.json \
            or not 'script' in request.json \
            or not 'user' in request.json:
        abort(400)
    instances = get_json("instances")
    instance = filter(lambda t: t['id'] == int(request.json['instance']), instances)
    if len(instance) == 0:
        abort(404)
    return 0

def task_launch(task):
    monJob = job.myJob(task['id'])
    task['start'] = int(time.time())
    task['state'] = "CURRENT"

    monJob.start()
    return task

@app.route('/wsexec/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    tasks = get_json("tasks")
    return jsonify({'tasks': map(make_public_task, tasks)})

@app.route('/wsexec/tasks/<int:task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    tasks = get_json("tasks")
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task(task[0])})

@app.route('/wsexec/tasks', methods=['POST'])
@auth.login_required
def create_task():
    task_request_check(request)
    tasks = get_json("tasks")
    task = {
        'id': tasks[-1]['id'] + 1,
        'name': request.json['name'],
        'tag': request.json['tag'],
        'start': '',
        'end': '',
        'instance': int(request.json['instance']),
        'script': request.json['script'],
        'user': request.json['user'],
        'stdout': '',
        'stderr': '',
        'rc': '',
        'state': 'INIT'
    }
    task = task_launch(task)
    tasks.append(task)
    set_json("tasks", tasks)

    return jsonify({'task': make_public_task(task)}), 201

@app.route('/wsexec/tasks/<int:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    tasks = get_json("tasks")
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'start' in request.json and type(request.json['start']) != int:
        abort(400)
    if 'end' in request.json and type(request.json['end']) != int:
        abort(400)
    if 'stdout' in request.json and type(request.json['stdout']) != unicode:
        abort(400)
    if 'stderr' in request.json and type(request.json['stderr']) != unicode:
        abort(400)
    if 'rc' in request.json and type(request.json['rc']) != int:
        abort(400)
    if 'state' in request.json and type(request.json['state']) != unicode and not (
            request.json['state'] == "INIT" or
            request.json['state'] == "CURRENT" or
            request.json['state'] == "DONE" or
            request.json['state'] == "ABORT"):
        abort(400)
    task[0]['start'] = request.json.get('start', task[0]['start'])
    task[0]['end'] = request.json.get('end', task[0]['end'])
    task[0]['stdout'] = request.json.get('stdout', task[0]['stdout'])
    task[0]['stderr'] = request.json.get('stderr', task[0]['stderr'])
    task[0]['rc'] = request.json.get('rc', task[0]['rc'])
    task[0]['state'] = request.json.get('state', task[0]['state'])

    set_json("tasks", tasks)

    return jsonify({'task': make_public_task(task[0])})

"""
@app.route('/wsexec/tasks/<int:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    tasks = get_json("tasks")
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    set_json("tasks", tasks)
    return jsonify({'result': True})
"""
# __________________________________ instance __________________________________

def make_public_instance(instance):
    new_instance = {}
    for field in instance:
        if field == 'id':
            new_instance['uri'] = url_for('get_instance', instance_id=instance['id'], _external=True)
            new_instance[field] = instance[field]
        else:
            new_instance[field] = instance[field]
    return new_instance

def instance_request_check(request):
    if not request.json \
            or not 'ip' in request.json \
            or not 'tag' in request.json \
            or not 'state' in request.json:
        abort(400)
    return 0

@app.route('/wsexec/instances', methods=['GET'])
@auth.login_required
def get_instances():
    instances = get_json("instances")
    return jsonify({'instances': map(make_public_instance, instances)})

@app.route('/wsexec/instances/<int:instance_id>', methods=['GET'])
@auth.login_required
def get_instance(instance_id):
    instances = get_json("instances")
    instance = filter(lambda t: t['id'] == instance_id, instances)
    if len(instance) == 0:
        abort(404)
    return jsonify({'instance': make_public_instance(instance[0])})

@app.route('/wsexec/instances', methods=['POST'])
@auth.login_required
def create_instances():
    instance_request_check(request)
    instances = get_json("instances")
    instance = {
        'id': instances[-1]['id'] + 1,
        'ip': request.json['ip'],
        'tag': request.json['tag'],
        'state': request.json['state']
    }
    instances.append(instance)
    set_json("instances", instances)
    return jsonify({'instance': make_public_instance(instance)}), 201

@app.route('/wsexec/instances/<int:instance_id>', methods=['PUT'])
@auth.login_required
def update_instance(instance_id):
    instances = get_json("instances")
    instance = filter(lambda t: t['id'] == instance_id, instances)
    if len(instance) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'ip' in request.json and type(request.json['ip']) != unicode:
        abort(400)
    if 'tag' in request.json and type(request.json['tag']) != unicode:
        abort(400)
    if 'state' in request.json and type(request.json['state']) != unicode and not (
            request.json['state'] == "ACTIVE" or
            request.json['state'] == "DEACTIVATE"):
        abort(400)
    instance[0]['ip'] = request.json.get('ip', instance[0]['ip'])
    instance[0]['tag'] = request.json.get('tag', instance[0]['tag'])
    instance[0]['state'] = request.json.get('state', instance[0]['state'])

    set_json("instances", instances)

    return jsonify({'task': make_public_instance(instance[0])})

@app.route('/wsexec/instances/<int:instance_id>', methods=['DELETE'])
@auth.login_required
def delete_instance(instance_id):
    instances = get_json("instances")
    instance = filter(lambda t: t['id'] == instance_id, instances)
    if len(instance) == 0:
        abort(404)
    instances.remove(instance[0])
    set_json("instances", instances)
    return jsonify({'result': True})

# __________________________________ main __________________________________

if __name__ == '__main__':
    app.run(debug=True)