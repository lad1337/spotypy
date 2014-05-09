import requests
import time
import re
import json
import os
import sys
import mpylayer


mswin = os.name == "nt"

from urllib2 import urlopen, HTTPError

if sys.version_info[:2] >= (3, 0):
    # pylint: disable=E0611,F0401
    import pickle
    from urllib.request import build_opener
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode


else:
    from urllib2 import build_opener, HTTPError, URLError
    from urllib import urlencode
    import cPickle as pickle



def search(artist, song_title=""):
    print u"searching for: {} - {}".format(artist, song_title)
    found_songs = []
    bitrates = []

    return dosearch(u"{} {}".format(artist, song_title))
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

def dosearch(term):
    """ Perform search. """
    url = "http://pleer.com/search?q=%s&target=tracks&page=%s"
    url = url % (term.replace(" ", "+"), 1)
    try:
        wdata = requests.get(url)
        songs = get_tracks_from_page(wdata.text)
        if songs:
            return songs
        else:
            return []
    except Exception:
        return []


def get_tracks_from_page(page):
    """ Get search results from web page. """
    fields = "duration file_id singer song link rate size source".split()
    matches = re.findall(r"\<li.(duration[^>]+)\>", page)
    songs = []
    if matches:
        for song in matches:
            cursong = {}
            for f in fields:
                v = re.search(r'%s=\"([^"]+)"' % f, song)
                if v:
                    cursong[f] = tidy(v.group(1), f)
                    cursong["R" + f] = v.group(1)
                else:
                    break
            else:
                try:
                    cursong = get_average_bitrate(cursong)
                except ValueError: # cant convert rate to int: invalid literal for int() with base 10: '96 K'
                    continue
                # u'4.514 Mb'
                cursong['size'] = int(float(cursong['size'][:3]) * 1024.0 * 1024.0)
                songs.append(cursong)
                continue

    else:
        return False
    return songs

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
    if not "track_url" in song:
        url = 'http://pleer.com/site_api/files/get_url?action=download&id=%s'
        url = url % song['link']
        try:
            wdata = urlopen(url, timeout=30).read().decode("utf8")
        except Exception:
            time.sleep(2) # try again
            wdata = urlopen(url, timeout=7).read().decode("utf8")

        j = json.loads(wdata)
        track_url = j['track_link']
        return track_url
    else:
        return song['track_url']


opener = build_opener()
ua = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"
opener.addheaders = [("User-Agent", ua)]
urlopen = opener.open

MPLAYER = None


def playsong(song, failcount=0):
    """ Play song using config.PLAYER called with args config.PLAYERARGS."""

    # pylint: disable = R0912
    try:
        track_url = get_stream(song)
        song['track_url'] = track_url
    except:
        return False

    try:
        cl = opener.open(track_url, timeout=5).headers['content-length']
    except (IOError, KeyError):
        return False

    global MPLAYER
    MPLAYER = None
    MPLAYER = mpylayer.MPlayerControl(extra_args=["prefer-ipv4", track_url])
    return True

def stop():
    if not MPLAYER:
        return
    MPLAYER.stop()

def pause_pause():
    if not MPLAYER:
        return
    return MPLAYER.pause()


# https://code.google.com/p/mpylayer/wiki/AvailableCommandsAndProperties
def status():
    data = {"length": MPLAYER.length,
            "mute": MPLAYER.mute,
            "samplerate": MPLAYER.samplerate,
            "time_pos": MPLAYER.time_pos,
            "volume": MPLAYER.volume,
            "speed": MPLAYER.speed,
            "percent_pos": MPLAYER.percent_pos,
            "meta": {"album": MPLAYER.meta_album,
                     "artist": MPLAYER.meta_artist,
                     "title": MPLAYER.meta_title,
                     "track": MPLAYER.meta_track,
                     "year": MPLAYER.meta_year,

            }
    }
    return data
