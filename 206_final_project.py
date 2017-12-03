'''
Hannah Thoms
SI 206 Final Project
December 2017
'''

import json
import sqlite3
import facebook
#file with access tokens for apis
import api_info
import requests
import re
from datetime import *


#caching setup
CACHE_FNAME = "206_Final_Project_cache.json"
try:
	cachehand = open(CACHE_FNAME, "r")
	cachedata = cachehand.read()
	cachehand.close()
	CACHE_DICTION = json.loads(cachedata)
except:
	CACHE_DICTION = {}

#part 1: Facebook API
fb_access_token = api_info.fb_user_token



def get_event_info(query):
	#first checks to see if query is already in the cache file
	if query in CACHE_DICTION:
		#stores data from dictionary for query in list object
		events_info = CACHE_DICTION[query]
	#adds query to cache file if not there already
	else:
		#retrieves facebook data for the query
		events_info = graph.request(query)
		#saves event data for query in dictionary
		CACHE_DICTION[query] = events_info
		#opens cache file to write to it
		cachefile = open(CACHE_FNAME, "w")
		#writes data in the dictionary to the cache file
		cachefile.write(json.dumps(CACHE_DICTION))
		#closes cache file after writing
		cachefile.close()
	#should return list of data retrieved from the cache or pulled from facebook
	return events_info['data']

graph = facebook.GraphAPI(fb_access_token)
#search facebook for concerts
events = get_event_info('/search?q=concert&type=event&limit=100')

conn = sqlite3.connect('206_Final_project.sqlite')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS Event_Places')
cur.execute('CREATE TABLE Event_Places(place_id STRING PRIMARY KEY UNIQUE NOT NULL, city STRING, country STRING, latitude FLOAT, longitude FLOAT)')
cur.execute('DROP TABLE IF EXISTS Events')
cur.execute('CREATE TABLE Events(event_id STRING PRIMARY KEY UNIQUE NOT NULL, event_name STRING, place_id STRING, start_time STRING, day_of_week INTEGER, num_attending INTEGER, num_interested INTEGER, FOREIGN KEY(place_id) REFERENCES Event_Places(place_id))')

def return_info1(attr1, json_object):
	if attr1 in json_object:
		return json_object[attr1]
	else:
		return None

def return_info2(attr1, attr2, json_object):
	if attr1 in json_object and attr2 in json_object[attr1]:
		return json_object[attr1][attr2]
	else:
		return None

count = 0
#get more information about each event by requesting each event's page
#store it into 
for event in events:
	eventid = events[count]['id']
	event_info = graph.get_object(id=events[count]['id'], fields='name, place, start_time, attending_count, interested_count')
	#facebook date format (2017-12-09T18:00:00+0700) to day of week where monday = 0 and sunday = 6
	if 'place' in event_info:
		place_tup = (return_info2('place', 'id', event_info), return_info2('location', 'city', event_info['place']), return_info2('location', 'country', event_info['place']), return_info2('location', 'latitude', event_info['place']), return_info2('location', 'longitude', event_info['place']))
		cur.execute('INSERT OR IGNORE INTO Event_Places(place_id, city, country, latitude, longitude) VALUES(?,?,?,?,?)', place_tup)
	if 'start_time' in event_info:
		timestamp = event_info['start_time']
		ymd = re.match('^.{10}', timestamp).group(0).split('-')
		dayofweek = date(int(ymd[0]), int(ymd[1]), int(ymd[2])).weekday()
	else: 
		dayofweek = None
	event_tup = (eventid, return_info1('name', event_info), return_info2('place', 'id', event_info), return_info1('start_time', event_info), dayofweek, return_info1('attending_count', event_info), return_info1('interested_count', event_info))
	cur.execute('INSERT OR IGNORE INTO Events(event_id, event_name, place_id, start_time, day_of_week, num_attending, num_interested) VALUES (?, ?, ?, ?, ?, ?, ?)', event_tup)

	count += 1
conn.commit()





#DarkSky API



#Google Maps API



#Gmail API

