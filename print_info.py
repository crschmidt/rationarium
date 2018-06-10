#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib
import sys
import random

def get_video_length(video_info):
    t = video_info['contentDetails']['duration']
    t = t.replace("PT", "")
    hour = minutes = secs = 0
    bits = {}
    for bit in ['H', 'M', 'S']:
        if bit in t:
            x, t = t.split(bit)
            bits[bit] = int(x)
    
    seconds = int(bits.get('H', 0))*3600  + bits.get('M', 0) * 60 + bits.get('S', 0)
    return seconds

playlist = sys.argv[1]

pageToken = ""
ids = []
while pageToken != None:
    url = "https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&key=AIzaSyAyVxBfBgKYhceM7DesiPNfih9lRGZA5vg&playlistId=%s" % playlist
    if pageToken:
        url = "%s&pageToken=%s" % (url, pageToken)
    print url    
    data = json.load(urllib.urlopen(url))
    for i in data['items']:
        ids.append(i['contentDetails']['videoId']) #, i['id']])
    pageToken = data.get('nextPageToken')
    print data['pageInfo'], data.get('nextPageToken')
print ",".join(ids)
ids2 = ids[:]
random.shuffle(ids2)
print "random", "http://www.youtube.com/watch_videos?video_ids=%s" % ",".join(ids2[0:10])
items = []
#sys.exit()
for i in range(0, len(ids), 50):
    joined_vids = ",".join(ids[i:i+50])
    url = "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&maxResults=50&id=%s&key=AIzaSyAyVxBfBgKYhceM7DesiPNfih9lRGZA5vg" % joined_vids
    response = urllib.urlopen(url).read()
    data = json.loads(response.decode("utf-8"))
    for item in data['items']:
        items.append(item)
        seconds = get_video_length(item)
        if seconds > 1800:
            print item['id'], item['snippet']['title']

s = []
chans = []

for i in items:
    chans.append(i['snippet']['channelId'])
    seconds = get_video_length(i)
    s.append(seconds)

#    continue
#print ", ".join(set(chans))
print s, sum(s)
