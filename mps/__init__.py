import requests
import time
import re
import json
import os
import sys
import logging
from mpd import MPDClient

logger = logging.getLogger("mps")


MPD = MPDClient()
MPD.connect("localhost", 6600)
mswin = os.name == "nt"
current_milli_time = lambda: int(round(time.time() * 1000))
UA = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"

from urllib2 import urlopen

if sys.version_info[:2] >= (3, 0):
    # pylint: disable=E0611,F0401
    from urllib.request import build_opener
    from urllib import quote_plus


else:
    from urllib2 import build_opener
    from urllib import quote_plus


def search(artist, song_title=u""):
    logging.debug(u"searching for: {} - {}".format(artist, song_title))
    search_term = u"{} {}".format(artist, song_title)
    
    return dosearch(search_term)
    best_song = None
    best_song_score = (0, 0)
    for song_version in song_versions:
        rate = song_version["rate_int"]
        size = song_version["size"]
        if (size, rate) > best_song_score:
            best_song_score = (size, rate)
            best_song = song_version
    if best_song:
        found_songs.append(best_song)
        bitrates.append(best_song["rate_int"])
    else:
        return []

    return found_songs

# parts of pms where used to make this
"""
pms.

https://github.com/np1/pms

Copyright (C)  2013 nagev

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

def as_json(text):
    startidx = text.find('(')
    endidx = text.rfind(')')
    return json.loads(text[startidx + 1:endidx])


def dosearch(term):
    """ Perform search. """
    # https://databrainz.com/api/search_api.cgi?jsoncallback=jQuery1111010430388749936614_1529588452356&qry=mario&format=json&mh=50&where=mpl&r=&y=0721190802155c415d5c405d5d445f5d435455475854495f5b465d59&_=1529588452358
    url = "https://databrainz.com/api/search_api.cgi"
    try:
        wdata = requests.get(url, params={
            "format": "json",
            "jsoncallback": "jQuery1111010430388749936614_1529588452356",
            "mh": 50,
            "qry": term.strip(),
            "where": "mpl",
            '_': current_milli_time(),
        })

        search = as_json(wdata.text)
        songs = []
        for song in search['results']:
            songs.append({
                'duration': song['time'],
                'size': int(float(song['size'])),
                'file_id': song['url'],
                'singer': song['artist'],
                'song': song['title'],
                'albumart': song['albumart'],
                'album': song['album'],
            })

        return songs
    except Exception as e:
        print e
        return []


def get_average_bitrate(song):
    """ calculate average bitrate of VBR tracks. """
    if song["rate"] == "VBR":
        vbrsize = float(song["Rsize"][:-3]) * 10000
        vbrlen = float(song["Rduration"])
        vbrabr = str(int(vbrsize / vbrlen))
        song["listrate"] = vbrabr + " v" # for display in list
        song["rate"] = vbrabr + " Kb/s VBR" # for playback display
    else:
        song["listrate"] = song["rate"][:3] # not vbr list display
    song["rate_int"] = int(song["rate"][:4])

    return song


def tidy(raw, field):
    """ Tidy HTML entities, format songlength if field is duration.  """
    if field == "duration":
        raw = time.strftime('%M:%S', time.gmtime(int(raw)))
    else:
        for r in (("&#039;", "'"), ("&amp;#039;", "'"), ("&amp;amp;", "&"),
                 ("  ", " "), ("&amp;", "&"), ("&quot;", '"')):
            raw = raw.replace(r[0], r[1])
    return raw


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


opener = build_opener()
opener.addheaders = [("User-Agent", UA)]
urlopen = opener.open

MPLAYER = None


def playsong(song, failcount=0):
    """ Play song using config.PLAYER called with args config.PLAYERARGS."""

    # pylint: disable = R0912
    try:
        track_url = get_stream(song)
        song['track_url'] = track_url
    except Exception as e:
        print e
        return False

    try:
        cl = opener.open(track_url, timeout=5).headers['content-length']
    except (IOError, KeyError):
        return False
    MPD.clear()
    print "playing", track_url
    MPD.add(track_url)
    MPD.play(0)
    MPD.consume(1)
    return True


def stop():
    MPD.stop()


def pause_pause():
    return MPD.pause()


# https://code.google.com/p/mpylayer/wiki/AvailableCommandsAndProperties
def status():
    return MPD.status()

