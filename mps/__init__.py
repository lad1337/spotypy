import requests
import time
import json
import os
import logging
import math

from mpd import MPDClient
import pafy


logger = logging.getLogger("mps")


MPD = MPDClient()
MPD.connect("localhost", 6600)
mswin = os.name == "nt"
current_milli_time = lambda: int(round(time.time() * 1000))
UA = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"


def search(artist, song_title=u""):
    logging.debug(u"searching for: {} - {}".format(artist, song_title))
    search_term = u"{} {}".format(artist, song_title).strip()
    if "youtu" in search_term:
        return do_yt_search(search_term)
    return dosearch(search_term)


def as_json(text):
    startidx = text.find('(')
    endidx = text.rfind(')')
    return json.loads(text[startidx + 1:endidx])


def convert_size(size_bytes):
    if size_bytes == 0:
       return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def do_yt_search(url):
    video = pafy.new(url)
    audio = video.getbestaudio()
    size = audio.get_filesize()
    song = {
        'duration': video.duration.strip('0:'),
        'size': int(size),
        'file_id': video.videoid,
        'track_url': audio.url,
        'singer': video.author,
        'song': video.title,
        'cover_url': video.thumb,
        'album': video.author,
    }
    return [song]


def dosearch(term):
    """ Perform search. """
    # https://databrainz.com/api/search_api.cgi?jsoncallback=jQuery1111010430388749936614_1529588452356&qry=mario&format=json&mh=50&where=mpl&r=&y=0721190802155c415d5c405d5d445f5d435455475854495f5b465d59&_=1529588452358
    url = "https://databrainz.com/api/search_api.cgi"
    try:
        wdata = requests.get(url, params={
            "format": "json",
            "jsoncallback": "jQuery1111010430388749936614_1529588452356",
            "mh": 50,
            "qry": term,
            "where": "mpl",
            '_': current_milli_time(),
        })
        try:
            search = as_json(wdata.text)
        except ValueError:
            logger.debug("text: {}".format(wdata.text))
            raise
        songs = []
        for song in search['results']:
            songs.append({
                'duration': convert_size(float(song['size'])),
                'size': int(song['size']),
                'file_id': song['url'],
                'singer': song['artist'],
                'song': song['title'],
                'cover_url': song['albumart'],
                'album': song['album'],
            })

        return songs
    except Exception as e:
        logger.exception("fuck")
        return []


def get_stream(song):
    """ Return the url for a song. """

    url = 'https://databrainz.com/api/data_api_new.cgi'
    wdata = requests.get(
        url,
        params={
            'jsoncallback': 'jQuery1111046508799818694146_1529589898496',
            'id': song['file_id'],
            'r': 'mpl',
            'format': 'json',
            '_': current_milli_time(),
        },
        headers={"User-Agent": UA},
    )
    song = as_json(wdata.text)
    return song['song']['url']


def playsong(song, failcount=0):
    if 'track_url' not in song:
        try:
            track_url = get_stream(song)
            song['track_url'] = track_url
        except Exception:
            logger.exception()
            return False
    else:
        track_url = song['track_url']

    MPD.clear()
    logger.debug("playing {}".format(track_url))
    MPD.add(track_url)
    MPD.play(0)
    MPD.consume(1)
    return True


def stop():
    MPD.stop()


def pause_pause():
    return MPD.pause()


def status():
    return MPD.status()

