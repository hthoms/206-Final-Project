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


graph = facebook.GraphAPI(fb_access_token)
#search facebook for concerts
events = graph.request('/search?q=concert&type=event&limit=100')
#turn json info into dict
eventlist = events['data']

#events_info 
count = 0
#get more information about each event by requesting each event's page
#store it into 
for event in eventlist:
	eventid = eventlist[count]['id']
	event_info = graph.get_object(id=eventlist[count]['id'], fields='name, place, start_time, attending_count, interested_count', args=["date_format=U"])
	print(json.dumps(event_info, indent=4))
	timestamp = event_info['start_time']

	#facebook date format to day of week
	ymd = re.match('^.{10}', timestamp).group(0).split('-')
	#returns the day of the week where monday = 0 and sunday = 6
	dayofweek = date(int(ymd[0]), int(ymd[1]), int(ymd[2])).weekday()
	print(dayofweek)

	count += 1


#start time into usable date format ex 2018-10-20T19:00:00-0400

#event_date = 
