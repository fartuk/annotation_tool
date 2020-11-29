from __main__ import app
from flask import Flask, render_template, request
import json
import os
import numpy as np
import datetime



@app.route('/')
def index():
    return render_template('index.html')  


@app.route('/room/<string:room_token>')
def room(room_token):
    return render_template('room.html', room_token=room_token)  


@app.route('/task/<string:annotator_token>')
def task(annotator_token):
    return render_template('task.html', annotator_token=annotator_token)  


@app.route('/text_info/<string:room_token>/<string:text_id>')
def text_info(room_token, text_id):
    return render_template('text_info.html', room_token=room_token, text_id=text_id)  


@app.route('/annotators_statistic/<string:room_token>')
def annotators_statistic(room_token):
    return render_template('annotators_statistic.html', room_token=room_token)  


