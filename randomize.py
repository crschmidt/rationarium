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

#httplib2.debuglevel =2  

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


#args = argparser.parse_args()

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

import pprint
import random

def run(playlist):
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
            ids.append([i['contentDetails']['videoId'], i['id']])
        pageToken = data.get('nextPageToken')
        print data['pageInfo'], data.get('nextPageToken')
    random.shuffle(ids)
    for ordinal, id in enumerate(ids):
        item = {
            'id': id[1],
            'snippet': {
                'playlistId': playlist,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': id[0]
                },
                'position': ordinal
            }
        }
        pl_item = json.dumps(item)
        meta, response = http.request("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", method="PUT", body=pl_item, headers={"Content-Type": "application/json"})
#        print response

if __name__ == "__main__":
    playlist = sys.argv[1]
    run(playlist)
