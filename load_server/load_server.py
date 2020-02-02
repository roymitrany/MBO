import threading

import numpy as np
from flask import Flask
from flask_restplus import Api, Resource, fields, abort
import time
import argparse
from queue import Queue

class LoadTask:
    def __init__(self, task_index, task_load, start_time, res_event):
        self.index = task_index
        self.load_level = task_load
        self.tart_time = start_time
        self.end_time = 0
        self.result_event = res_event

counter = 0
num_of_tasks = 0
tasks_queue: Queue = Queue()
app = Flask(__name__)

api = Api(app, version='1.0', title='CPU Loader', description='loading app',
          contact_email='roym@technion.ac.il', contact='Roy Mitrany')
ns = api.namespace('load', description='CPU Loader')

srv_state_concurrent = api.model('ServerState', {
    'completed_tasks': fields.String(required=True, description='Number of completed tasts since start'),
    'duration': fields.String(required=False, description='Duration of last task')})

srv_state_queue = api.model('ServerState', {
    'completed_tasks': fields.String(required=True, description='Number of completed tasts since start'),
    'queue_size_enqueue': fields.String(required=True, description='Number of tasks in server, when the task arrived, including current task'),
    'queue_size_task_end': fields.String(required=True, description='Number of tasks in server, when the task ended, excluding current task'),
    'duration': fields.String(required=False, description='Duration of last task')})

def load_cpu(level):
    global num_of_tasks
    num = level*100000
    a_list = range(0,num)
    num_of_tasks += 1
    for i in a_list:
        fl = float(i/num)
        tfl = np.tanh(fl)
    num_of_tasks -= 1


def dequeue_load_cpu():
    global tasks_queue
    while True:
        task_obj = tasks_queue.get()
        load_cpu(task_obj.load_level)
        # Notify the main load function that the task is completed
        task_obj.result_event.set ()


@ns.route('/queue_load/<int:level>')
@ns.param('level', description='Load Level')
@ns.response(400, 'Invalid operation')
@ns.response(503, 'Server Too busy')
class QueueLoad(Resource):
    # Trying to define a static variable
    #counter = 0
    @ns.doc('queue_load_cpu')
    @ns.marshal_with(srv_state_queue)
    @ns.response(200, 'Success')
    def get(self, level):
        """Insert a new load task to queue """
        global counter
        state = {}
        begin_ts = time.time ()
        res_event = threading.Event ()
        task_obj = LoadTask(counter, level, begin_ts, res_event)
        # Tell how long is the queue
        q_size_enqueue = 1 #If nothing is running, our task is the only one in the system, so queue size is 1
        if num_of_tasks>0:
            q_size_enqueue = tasks_queue.qsize() + 2 # There is something running, plus our task plus all the waiting tasks to the queue

        # If the queue is too long, return an error
        #print (str(tasks_queue.qsize()))
        if tasks_queue.qsize() >= 8:
            abort (503,message="Server overloaded, queue size is: "+str(tasks_queue.qsize()))
        tasks_queue.put (task_obj)
        res_event.wait (timeout=60)
        end_ts = time.time ()
        duration_in_millis = int(1000*(end_ts-begin_ts))
        counter += 1
        queue_size_task_end = tasks_queue.qsize() + num_of_tasks #This value shows the queue size after the task is completed, excluding current task
        state['completed_tasks'] = counter
        state['queue_size_enqueue'] = q_size_enqueue
        state['queue_size_task_end'] = queue_size_task_end
        state['duration'] = str(duration_in_millis)
        return state


@ns.route('/ping')
class Ping(Resource):
    @ns.doc('test_liveness')
    @ns.marshal_with(srv_state_concurrent)
    @ns.response(200, 'Success', srv_state_concurrent)
    def get (self):
        global counter
        state = {'completed_tasks': counter}
        return state

@ns.route('/reset_tasks_counter')
class ResetCounter(Resource):
    @ns.doc('reset the completed tasks counter. More convenient that restarting the server')
    @ns.marshal_with(srv_state_concurrent)
    @ns.response(200, 'Success', srv_state_concurrent)
    def get (self):
        global counter
        counter = 0
        state = {'completed_tasks': counter}
        return state

if __name__ == '__main__':
    parser = argparse.ArgumentParser (
        description='MMMMMMM',
    )
    parser.add_argument ('port', type=int)
    args = parser.parse_args ()
    port = args.port

    # Run a separate thread that enqueues the tasks queue
    t = threading.Thread (target=dequeue_load_cpu)
    t.start ()

    app.run(debug=True, host = '0.0.0.0', port=port)
