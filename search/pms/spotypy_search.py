#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import re
import time
import json
import requests
import sys
import urllib2
mswin = os.name == "nt"

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
    except Exception as e:
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
                cursong['title'] = cursong["song"]
                cursong['file_uri'] = 'http://pleer.com/site_api/files/get_url?action=download&id=%s' % cursong['link']
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        help="the search term",
        type=str,
        dest="search",
        default=False
    )
    parser.add_argument(
        "--get_link",
        help="json song data",
        type=str,
        default=False
    )
    args = parser.parse_args()
    if args.search:
        print json.dumps({"songs": dosearch(args.search), "id": "pms"})
    elif args.get_link:
        print json.dumps()
