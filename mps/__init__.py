import requests
import time
import re
import json
import os
import sh
import mpylayer
import fnmatch
import uuid



def dosearch(term):
    matches = []
    for root, dirnames, filenames in os.walk('search'):
      for filename in fnmatch.filter(filenames, 'spotypy_search.*'):
          matches.append(os.path.abspath(os.path.join(root, filename)))

    songs = []
    for script_path in matches:
        run = sh.Command(script_path)
        out = run(s=term)
        print out, type(out)
        data = json.loads(unicode(out))
        for song in data["songs"]:
            song["script"] = script_path
            song["uuid"] = str(uuid.uuid4())
            songs.append(song)
    return songs


def search(artist, song_title=""):
    print u"searching for: {} - {}".format(unicode(artist), unicode(song_title))

    return dosearch(u"{} {}".format(unicode(artist), unicode(song_title)))


MPLAYER = None


def playsong(song, failcount=0):
    """ Play song using config.PLAYER called with args config.PLAYERARGS."""

    # pylint: disable = R0912

    global MPLAYER
    MPLAYER = None
    MPLAYER = mpylayer.MPlayerControl(extra_args=["prefer-ipv4", song["file_uri"]])
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
