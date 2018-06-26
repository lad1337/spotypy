#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import json
import uuid
import time
import mps
import requests
from threading import Lock
from bottle import Bottle, static_file, response, request
from bs4 import BeautifulSoup

import logging
import sys
logger = logging.getLogger("spotypy")


application = Bottle()

HISTORY = {}
HISTORY_IDS = []
CURRENT = {}
QUEUE = {}
QUEUE_IDS = []


q_lock = Lock()


class QueueItem(object):
    
    def __init__(self, uuid, vote_count=0):
        self.uuid = uuid
        self.vote_count = vote_count

    def __eq__(self, other):
        return self.uuid - other.uuid


def check_q():
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS, q_lock
    with q_lock:
        status = mps.status()
        if status["state"] == "stop":
            _fucking_next()
            return

        if _percent() > 99:
            _stop()
    return status


def _fucking_next():
    if QUEUE_IDS and QUEUE:
        _start_song(QUEUE[QUEUE_IDS[0].uuid])
        time.sleep(1)


def _start_song(song_data):
    logging.debug(u"starting song {singer} - {song} {duration}".format(**song_data))
    result = mps.playsong(song_data)
    if result:
        _play(song_data)
    else:
        _remove_from_q(song_data)
    return result


def _play(song_data):
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS
    if "uuid" not in song_data:
        song_data["uuid"] = str(uuid.uuid4())
    _remove_from_q(song_data)

    if CURRENT:
        _add_to_history(CURRENT)
    if "cover_url" not in song_data:
        cover_url = _steal_image(song_data)
        song_data["cover_url"] = cover_url
    CURRENT = song_data


def _stop():
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS
    if CURRENT:
        _add_to_history(CURRENT)
    CURRENT = {}


def _add_to_history(son_data):
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS
    HISTORY[son_data["uuid"]] = son_data
    HISTORY_IDS.append(CURRENT["uuid"])
    if len(HISTORY_IDS) > 10:
        HISTORY_IDS = HISTORY_IDS[1:]
        HISTORY = {uuid: HISTORY[uuid] for uuid in HISTORY_IDS}


def _add_to_q(song_data):
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS
    if "uuid" not in song_data:
        song_data["uuid"] = str(uuid.uuid4())
    s_uuid = song_data["uuid"]
    if not _find_song_in_queue(s_uuid):
        QUEUE[s_uuid] = song_data
        QUEUE_IDS.append(QueueItem(s_uuid))


def _remove_from_q(song_data):
    global CURRENT, QUEUE, QUEUE_IDS, HISTORY, HISTORY_IDS
    s_uuid = song_data["uuid"]
    song = _find_song_in_queue(s_uuid)
    if song is not None:
        QUEUE_IDS.remove(song)
    if s_uuid in QUEUE:
        del QUEUE[s_uuid]


def _steal_image(song_data):
    term = u"{singer} {song} album cover".format(**song_data)
    # https://www.google.de/search?q=Emil+Bulls+-+Here+Comes+the+Fire&tbm=isch
    payload = {"tbm": "isch", "q": term}
    r = requests.get("https://www.google.de/search", params=payload)
    soup = BeautifulSoup(r.text)
    img = soup.find("img")
    if img is None:
        return ""
    return img["src"]


@application.get('/ping')
def ping_get():
    return {'reply': 'pong'}


@application.get('/')
def index():
    return static_file("index.html", root=os.path.join(os.path.abspath("./"), "html"))


@application.get('/<filename>')
def files(filename):
    return static_file(filename, root=os.path.join(os.path.abspath("./"), "html"))


@application.get('/search')
def search():
    params = bottle.request.params
    result = mps.search(unicode(params["term"], encoding='utf-8'))
    for r in result:
        if "uuid" not in r:
            r["uuid"] = str(uuid.uuid4())
    response.content_type = 'application/json'
    return json.dumps(result)


@application.post('/play')
def play_song():
    song_data = json.loads(request.body.read())
    result = _start_song(song_data)
    response.content_type = 'application/json'
    return json.dumps({"result": result})


@application.get('/current')
def current():
    global CURRENT
    response.content_type = 'application/json'
    return json.dumps(CURRENT)


@application.get('/history')
def history():
    global HISTORY, HISTORY_IDS
    response.content_type = 'application/json'
    return json.dumps([HISTORY[uuid] for uuid in HISTORY_IDS])


@application.get('/queue')
def queue():
    global QUEUE, QUEUE_IDS
    response.content_type = 'application/json'
    results = []
    for queue_item in QUEUE_IDS:
        song = QUEUE[queue_item.uuid]
        song['votecount'] = queue_item.vote_count
        results.append(song)
    return json.dumps(results)


@application.put('/queue')
def add_queue():
    global QUEUE_IDS
    song_data = json.loads(request.body.read())
    _add_to_q(song_data)
    QUEUE_IDS = sorted(
        QUEUE_IDS, key=lambda q: q.vote_count, reverse=True)
    response.content_type = 'application/json'
    return json.dumps(QUEUE)


def _find_song_in_queue(uuid):
    global QUEUE_IDS
    for song in QUEUE_IDS:
        if song.uuid == uuid:
            return song


def voter(func):
    def wrapper(*args, **kwargs):
        global QUEUE_IDS
        song_data = json.loads(request.body.read())
        song = _find_song_in_queue(song_data['uuid'])
        func(song)
        if song.vote_count <= -10:
            _remove_from_q(song_data)

        QUEUE_IDS = sorted(
            QUEUE_IDS, key=lambda q: q.vote_count, reverse=True)
        response.content_type = 'application/json'
        return json.dumps(song.vote_count)
    return wrapper
        

@application.put('/voteup')
@voter
def vote_up(song):
    logging.debug("Vote up song with uuid={}".format(song.uuid))
    song.vote_count += 1 


@application.put('/votedown')
@voter
def vote_down(song):
    logging.debug("Vote down song with uuid={}".format(song.uuid))
    song.vote_count -= 1


@application.get('/play')
def play_song():
    global QUEUE, QUEUE_IDS
    result = mps.pause_pause()
    if not result:
        _fucking_next()
    response.content_type = 'application/json'
    return json.dumps({"result": result})


@application.get('/stop')
def stop():
    result = mps.stop()
    _stop()
    response.content_type = 'application/json'
    return json.dumps({"result": result})


@application.get('/pause')
def pause():
    global QUEUE, QUEUE_IDS
    result = mps.pause()
    if not result:
        _fucking_next()
    response.content_type = 'application/json'
    return json.dumps({"result": result})


@application.get('/next')
def next():
    _fucking_next()


@application.get('/prev')
def prev():
    global HISTORY, HISTORY_IDS
    if HISTORY and HISTORY_IDS:
        _start_song(HISTORY[HISTORY_IDS[-1]])


@application.get('/status')
def status():
    status = check_q()
    response.content_type = 'application/json'
    return json.dumps(status)


def _percent():
    if not CURRENT:
        return 0
    status = mps.status()
    elapsed = 0
    if "elapsed" in status:
        elapsed = float(status["elapsed"])
    duration = 1
    if "duration" in status:
        duration = float(status["duration"])
    return (elapsed / duration) * 100


@application.post('/status')
def set_stats():
    status = json.loads(request.body.read())
    for key, value in status.items():
        getattr(mps.MPD, key)(value)
    response.content_type = 'application/json'
    return json.dumps({})


if __name__ == "__main__":
    import bottle

    logging.basicConfig()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    root.addHandler(ch)

    try:
        bottle.run(application, host="0.0.0.0", port="9000", reloader=True)
    except:
        raise
    finally:
        try:
            mps.MPD.stop()
            mps.MPD.close()
        except:
            pass
