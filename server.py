from flask import Flask, render_template, request
from flask_cors import cross_origin
import os
import numpy as np
import json
import datetime
import time
import queue
from uuid import uuid4
from utils import *

app = Flask(__name__)
import frontend


global text_id
global tasks
tasks = []
global task_queue
task_queue = queue.Queue()
global text_start_time
text_start_time =  int(time.time())


@app.route('/test_get', methods=['get'])
@cross_origin()
def test_get():
    resp = {}
    resp["hello"] = "hello"
    return resp

@app.route('/create_room', methods=['post', 'get'])
@cross_origin()
def create_room():
    room_type = request.json.get('room_type')
    class_names = request.json.get('class_names')
    room_token = str(uuid4())
    
    room_json = {}
    room_json["room_token"] = room_token
    room_json["room_type"] = room_type
    room_json["class_names"] = class_names
    room_json["annotator_tokens"] = []
    room_json["text_ids"] = []
    room_json["task_queue"] = []


    os.makedirs("data/rooms", exist_ok=True)
    os.makedirs("data/annotators", exist_ok=True)
    os.makedirs("data/texts", exist_ok=True)
    os.makedirs("data/tasks", exist_ok=True)

    save_json("data/rooms/{}.json".format(room_token), room_json)   
    
    return room_json



@app.route('/create_annotator', methods=['post', 'get'])
@cross_origin()
def create_annotator():
    room_token = request.json.get('room_token')
    room_json = load_json("data/rooms/{}.json".format(room_token))

    annotator_json = {}
    annotator_json["annotator_token"] = str(uuid4())
    annotator_json["room_token"] = room_token
    annotator_json["task_ids"] = []

    room_json['annotator_tokens'].append(annotator_json["annotator_token"])
    
    save_json("data/annotators/{}.json".format(annotator_json["annotator_token"]), annotator_json)
    save_json("data/rooms/{}.json".format(room_token), room_json)
    
    return annotator_json



@app.route('/room_info', methods=['post', 'get'])
@cross_origin()
def room_info():
    room_token = request.json.get('room_token')
    room_json = load_json("data/rooms/{}.json".format(room_token))
    
    return room_json


    
@app.route('/add_text', methods=['post', 'get'])
@cross_origin()
def add_text():
    text_json = json.loads(request.data)
    text_json['text_id'] = str(uuid4())
    text_json['start_time'] = int(time.time())
    text_json['task_time'] = int(text_json['task_time'])
    text_json['task_ids'] = []

    room_json = load_json("data/rooms/{}.json".format(text_json["room_token"]))
    room_json['text_ids'].append(text_json['text_id'])
    
    word_tasks_list = text_to_word_tasks(text_json['text'], sent_cnt=int(text_json['sentences_per_task']))
    for word_task in word_tasks_list:
        task_json = {}
        task_json['room_token'] = text_json['room_token']
        task_json['start_time'] = int(text_json['start_time'])
        task_json['task_time'] = int(text_json['task_time'])
        task_json['task_id'] = str(uuid4())
        task_json['text_id'] = text_json['text_id']
        task_json['word_task'] = word_task
        task_json['status'] = TaskStatus.OPENED
        task_json['class_names'] = room_json['class_names']
        task_json['room_type'] = room_json['room_type']
    
        text_json['task_ids'].append(task_json['task_id'])
        room_json['task_queue'].append(task_json['task_id'])
        
        save_json('data/tasks/{}.json'.format(task_json['task_id']), task_json)
        
    save_json('data/texts/{}.json'.format(text_json['text_id']), text_json)  
    save_json('data/rooms/{}.json'.format(room_json['room_token']), room_json)

    return {"status":"OK"}



@app.route('/get_task', methods=['post', 'get'])
@cross_origin()
def get_task():
    annotator_token = request.json.get('annotator_token')
    annotator_json = load_json("data/annotators/{}.json".format(annotator_token))
    room_json = load_json('data/rooms/{}.json'.format(annotator_json['room_token']))
    if len(room_json['task_queue']) == 0:
        return {'status':TaskStatus.EMPTY}
    
    task_id = room_json['task_queue'][0]
    room_json['task_queue'] = room_json['task_queue'][1:]
    try:
        save_json('data/rooms/{}.json'.format(room_json['room_token']), room_json)
    except:
        None
    
    annotator_json['task_ids'].append(task_id)
    save_json('data/annotators/{}.json'.format(annotator_token), annotator_json)
    
    task_json = load_json('data/tasks/{}.json'.format(task_id))
    task_json['status'] = TaskStatus.ASSIGNED
    task_json['annotator_token'] = annotator_token
    task_json['work_start_time'] = int(time.time())

    save_json('data/tasks/{}.json'.format(task_id), task_json)

    return task_json


                
@app.route('/post_task', methods=['post', 'get'])
@cross_origin()
def post_task():
    task_id = request.json.get('task_id')
    word_task = request.json.get('word_task')
    task_json = load_json('data/tasks/{}.json'.format(task_id))
    task_json["word_task"] = word_task
    task_json["status"] = TaskStatus.FINISHED
    task_json["finish_time"] = int(time.time())

    save_json('data/tasks/{}.json'.format(task_json["task_id"]), task_json)  
    
    return {"status":"OK"}
    


@app.route('/text_result', methods=['post', 'get'])
@cross_origin()
def text_result():
    room_token = request.json.get('room_token')
    text_id = request.json.get('text_id')

    text_json = load_json("data/texts/{}.json".format(text_id))
    text_json['segments'] = []
    task_counts = {TaskStatus.OPENED:0, TaskStatus.ASSIGNED:0, TaskStatus.FINISHED:0}
    tasks_dir = 'data/rooms/{}/tasks/{}'.format(room_token, text_id)    
    for task_id in text_json["task_ids"]:
        task_json = load_json("data/tasks/{}.json".format(task_id))
        task_counts[task_json['status']] += 1
        task_segments = segments_from_task(text_json, task_json)
        text_json['segments'].extend(task_segments)
    
    for k, segment in enumerate(text_json['segments']):
        segment['segment_id'] = k
        
    text_json['task_counts'] = task_counts
    save_json('data/texts/{}.json'.format(text_id), text_json)
       
    return text_json



@app.route('/annotator_info', methods=['post', 'get'])
@cross_origin()
def annotator_info():
    annotator_token = request.json.get('annotator_token')
    annotator_json = load_json("data/annotators/{}.json".format(annotator_token))    
    
    return annotator_json



@app.route('/task_info', methods=['post', 'get'])
@cross_origin()
def task_info():
    task_id = request.json.get('task_id')
    task_json = load_json("data/tasks/{}.json".format(task_id))    
    
    return task_json



    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8005)

