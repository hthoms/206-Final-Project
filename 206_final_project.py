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
		print("usedcache")
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
		print("didn't use cache")
	#should return list of data retrieved from the cache or pulled from facebook
	return events_info['data']

graph = facebook.GraphAPI(fb_access_token)
#search facebook for concerts
events = get_event_info('/search?q=concert&type=event&limit=100')

conn = sqlite3.connect('206_Final_project.sqlite')
cur = conn.cursor()



count = 0
#get more information about each event by requesting each event's page
#store it into 
for event in events:
	eventid = events[count]['id']
	event_info = graph.get_object(id=events[count]['id'], fields='name, place, start_time, attending_count, interested_count')
	#print(json.dumps(event_info, indent=4))
	
	#facebook date format to day of week
	timestamp = event_info['start_time']
	ymd = re.match('^.{10}', timestamp).group(0).split('-')
	#returns the day of the week where monday = 0 and sunday = 6
	dayofweek = date(int(ymd[0]), int(ymd[1]), int(ymd[2])).weekday()
	print(dayofweek)

	count += 1


