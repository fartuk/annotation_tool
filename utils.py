import json
import time
import os
from uuid import uuid4




class TaskStatus:
    OPENED = 0
    ASSIGNED = 1
    FINISHED = 2
    EMPTY = -1

    
def save_json(path, data):
    with open(path, "w") as write_file:
        json.dump(data, write_file, ensure_ascii=False)   
        
        
def load_json(path):
    with open(path, "r") as read_file:
        in_data = json.load(read_file) 
        
    return in_data



def text_to_word_tasks(text, sent_cnt=2):
    tasks = []

    text = text.replace('\n', ' ')
    words = text.split(' ')

    sep_word_idxs = [idx for idx, word in enumerate(words) if  \
                         len(word) > 0 and word[-1] in '.?!' and (len(word) > 2 or word.lower() == word)]
    
    if len(sep_word_idxs) == 0:
        sep_word_idxs.append(len(words))
        
    used_sep_word_idxs = list(range(sent_cnt-1, len(sep_word_idxs), sent_cnt))
    if len(used_sep_word_idxs) == 0 or used_sep_word_idxs[-1] < len(sep_word_idxs) - 1:
        used_sep_word_idxs += [len(sep_word_idxs) - 1]

    last_word_end_idx = 0    
    for k in used_sep_word_idxs:
        end_word_idx = sep_word_idxs[k] + 1
        tasks.append([{"word_idx":idx, "word":word, "segmentation_idx":"off", "class":"off"} for idx, word in zip(range(last_word_end_idx, end_word_idx), words[last_word_end_idx:end_word_idx])])
        last_word_end_idx = end_word_idx
        
    return tasks

        

def segments_from_task(in_data, task_result):
    text = in_data['text']
    text = text.replace('\n', ' ')
    words = text.split(' ')

    task_segmentation_idxs = set([x['segmentation_idx'] for x in task_result['word_task']]).difference(set(['off']))
    segmentation_idxs_to_class = {x['segmentation_idx']:x['class'] for x in task_result['word_task']}

    segmentation_idxs_to_word_idx = {x:[] for x in task_segmentation_idxs}

    for word_task in task_result['word_task']:
        if word_task['segmentation_idx'] != 'off':
            segmentation_idxs_to_word_idx[word_task['segmentation_idx']].append(int(word_task['word_idx']))

    segment_arr = []
    for segmentation_idxs in task_segmentation_idxs:
        segment = {}
        start_word_idx = min(segmentation_idxs_to_word_idx[segmentation_idxs])
        end_word_idx = max(segmentation_idxs_to_word_idx[segmentation_idxs])
        segment['start_char'] = word_idx_to_char(words, start_word_idx)
        segment['end_char'] = word_idx_to_char(words, end_word_idx+1)-1
        segment['type'] = segmentation_idxs_to_class[segmentation_idxs]

        segment_arr.append(segment)
        
    return segment_arr        
        
        

def word_idx_to_char(words, idx):
    return sum([len(x) for x in words[:idx]]) + idx
















