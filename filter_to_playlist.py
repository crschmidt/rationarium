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

import httplib2
import os
import sys
import time
import json
import random

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube"

MISSING_CLIENT_SECRETS_MESSAGE = """configure"""

def get_authenticated_service():
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_READONLY_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)
  flow.params['approval_prompt'] = 'force'
  flow.params['authuser'] = '15'
  flow.params['access_type'] = 'offline'

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage)
  http = credentials.authorize(httplib2.Http())
  return http

def playlist_filter(video):
    if int(video['statistics']['viewCount']) > 1000:
        return True
    return False

def get_channel_ids(channel):
    http = get_authenticated_service()
    pageToken = ""
    ids = []
    while pageToken != None:
        url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=50&channelId=%s&type=video" % channel
        if pageToken:
            url = "%s&pageToken=%s" % (url, pageToken)
        status, response = http.request(url)
        data = json.loads(response)
        for i in data['items']:
            ids.append(i['id']['videoId'])
        pageToken = data.get('nextPageToken')
    return ids

def get_playlist_ids(playlist):
    http = get_authenticated_service()
    pageToken = ""
    ids = []
    while pageToken != None:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId=%s" % playlist
        if pageToken:
            url = "%s&pageToken=%s" % (url, pageToken)
        status, response = http.request(url)
        data = json.loads(response)
        for i in data['items']:
            ids.append(i['contentDetails']['videoId'])
        pageToken = data.get('nextPageToken')
    return ids

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

def video_display(item):
                seconds = get_video_length(item)
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                l = ""
                if h:
                    l = "%d:%02d:%02d" % (h, m, s)
                else:
                    l = "%d:%02d" % (m, s)
                return "%s (%s)" % (item['snippet']['title'], l)

def add_video(playlist, item):
        http = get_authenticated_service()
        item = {
            'snippet': {
                'playlistId': playlist,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': item['id']
                },
            }
        }
        pl_item = json.dumps(item)
        meta, response = http.request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", method="POST", body=pl_item, headers={"Content-Type": "application/json"})
        data = json.loads(response)
        if 'error' in data: 
            print data

def run(args):
    http = get_authenticated_service()
    pageToken = ""
    ids = []
    if args.playlist and args.channel:
        print "Specify only one of playlist or channel."
        return
    if args.playlist:
        ids = get_playlist_ids(args.playlist)
    if args.channel:
        ids = get_channel_ids(args.channel)
    exclude_ids = []
    if args.exclusions:
        for line in open(args.exclusions):
            exclude_ids.append(line.strip())
    print "Found %s items" % len(ids)
    filtered_ids = []
    for i in ids:
        if i not in exclude_ids:
            filtered_ids.append(i)
    print "Filtered to %s items" % len(filtered_ids)        
    playlist_items = []
    for i in range(0, len(filtered_ids), 50):
        joined_vids = ",".join(filtered_ids[i:i+50])
        url = "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&maxResults=50&id=%s" % joined_vids
        status, response = http.request(url)
        data = json.loads(response)
        for item in data['items']:
            if args.length or args.min_length:
                length = get_video_length(item)
                if args.min_length and length < args.min_length:
                    continue
                if args.length and length > args.length:
                    continue
                playlist_items.append(item)
            else:
                playlist_items.append(item)
    print "Found %s items after length filter" % len(playlist_items)
    if not args.norandom:
        random.shuffle(playlist_items)
    
    added = 0
    for ordinal, item in enumerate(playlist_items):
        if args.max_items and added >= args.max_items:
            break
        if args.ask:
            q = "Add %s?" % video_display(item) 
            a = raw_input(q)
            if a.lower() in ('y', 'yes'):
                add_video(args.target_playlist, item)
                if args.exclusions:
                    f = open(args.exclusions, "a")
                    f.write("%s\n" % item['id'])
                added += 1
        else:
            add_video(args.target_playlist, item)
            if args.exclusions:
                f = open(args.exclusions, "a")
                f.write("%s\n" % item['id'])
            added += 1
#        print response
    print "Added %s videos" % added

if __name__ == "__main__":
    argparser.add_argument("target_playlist", metavar="playlist")
    argparser.add_argument("--channel", metavar="channel")
    argparser.add_argument("--playlist", metavar="playlist")
    argparser.add_argument("--max_items", metavar="max", type=int)
    argparser.add_argument("--length", metavar="max", type=int)
    argparser.add_argument("--min_length", metavar="min", type=int)
    argparser.add_argument("--ask", action='store_true')
    argparser.add_argument("--norandom",  action='store_true')
    argparser.add_argument("--exclusions")

#    argparser.add_parameter("channel", metavar="channel")
    
    args = argparser.parse_args()
    run(args)
