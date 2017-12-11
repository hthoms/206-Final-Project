'''
Hannah Thoms
SI 206 Final Project
December 2017
'''

import json
import sqlite3
import facebook
import plotly.plotly as ply
import plotly.graph_objs as go
#file with access tokens for apis
import api_info
import requests
import re
from datetime import *
from PIL import Image
from io import BytesIO
import time

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

#function to make calls to facebook's api. stores json object in the cache
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
events = get_event_info('/search?q=concert&type=event&limit=200')

conn = sqlite3.connect('206_Final_project.sqlite')
cur = conn.cursor()
#creating databases for events and for the places those events are located in
cur.execute('DROP TABLE IF EXISTS Event_Places')
cur.execute('CREATE TABLE Event_Places(place_id STRING PRIMARY KEY UNIQUE NOT NULL, address STRING, city STRING, country STRING, latitude FLOAT, longitude FLOAT, temperature FLOAT, weather STRING)')
cur.execute('DROP TABLE IF EXISTS Events')
cur.execute('CREATE TABLE Events(event_id STRING PRIMARY KEY UNIQUE NOT NULL, event_name STRING, place_id STRING, start_time STRING, day_of_week INTEGER, num_attending INTEGER, num_interested INTEGER, FOREIGN KEY(place_id) REFERENCES Event_Places(place_id))')

#helper function
def return_info1(attr1, json_object):
	if attr1 in json_object:
		return json_object[attr1]
	else:
		return None
#helper function
def return_info2(attr1, attr2, json_object):
	if attr1 in json_object and attr2 in json_object[attr1]:
		return json_object[attr1][attr2]
	else:
		return None

#counter to iterate through event list
count = 0

for event in events:
	eventid = events[count]['id']
	event_info = graph.get_object(id=events[count]['id'], fields='name, place, start_time, attending_count, interested_count')
	#facebook date format (2017-12-09T18:00:00+0700) to day of week where monday = 0 and sunday = 6
	#inserts an event's place into the Event_places database if it exists
	if 'place' in event_info:
		place_tup = (return_info2('place', 'id', event_info), None, return_info2('location', 'city', event_info['place']), return_info2('location', 'country', event_info['place']), return_info2('location', 'latitude', event_info['place']), return_info2('location', 'longitude', event_info['place']), None, None)
		cur.execute('INSERT OR IGNORE INTO Event_Places(place_id, address, city, country, latitude, longitude, temperature, weather) VALUES(?,?,?,?,?,?,?,?)', place_tup)
	#gets the day of the week an event occurs on if a start time is provided
	if 'start_time' in event_info:
		timestamp = event_info['start_time']
		ymd = re.match('^.{10}', timestamp).group(0).split('-')
		dayofweek = date(int(ymd[0]), int(ymd[1]), int(ymd[2])).weekday()
	else: 
		dayofweek = None
	#inserting event information into the Events  database
	event_tup = (eventid, return_info1('name', event_info), return_info2('place', 'id', event_info), return_info1('start_time', event_info), dayofweek, return_info1('attending_count', event_info), return_info1('interested_count', event_info))
	cur.execute('INSERT OR IGNORE INTO Events(event_id, event_name, place_id, start_time, day_of_week, num_attending, num_interested) VALUES (?, ?, ?, ?, ?, ?, ?)', event_tup)

	count += 1
conn.commit()


#visualization 1 with plotly: number of events per day of week
cur.execute('SELECT day_of_week FROM Events')
#list of the days of the week events occur on
dayslist = cur.fetchall()

#list of frequencies of an event occurring on a day of the week. sumdays[0] = monday sumdays[6]=sunday
sumdays = [0, 0, 0, 0, 0, 0, 0]

#iterates through returned info from database, adding 1 to each day in the list of frequencies each time it sees a day 0-6
for day in dayslist:
	sumdays[day[0]] +=1
daylabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

#plotly setup
fbsumdata = [go.Bar(x=daylabels, y= sumdays, text = sumdays, textposition = 'auto', marker=dict(color='rgb(109, 132, 180)',line=dict(color='rgb(0,0,0)',width=1.5)))]
fbsumlayout=go.Layout(title="Number of Facebook Events Per Day of the Week", xaxis={'title':'Days of the Week'}, yaxis={'title':'Number of Events'})
fbsumfigure=go.Figure(data=fbsumdata,layout=fbsumlayout)
ply.iplot(fbsumfigure, filename='Facebook Events per day of the week')




#visualization 2 with plotly: average interested vs attending for events on each day of the week
#creates a list of info about the day of the week events occur on, and the number interested and attending
cur.execute('SELECT day_of_week, num_interested, num_attending FROM Events')
daysnums = cur.fetchall()

# the sum of people attending/interested in events for each day of the week, 0-6, mon-sun
interestedsum = [0, 0, 0, 0, 0, 0, 0]
attendingsum = [0, 0, 0, 0, 0, 0, 0]
for tup in daysnums:
	# day = number interested
	interestedsum[tup[0]] += tup[1]
	# day = number attending
	attendingsum[tup[0]] += tup[2]

#new lists for the averages for each day
interestedavg = [0, 0, 0, 0, 0, 0, 0]
attendingavg = [0, 0, 0, 0, 0, 0, 0]

for i in range(0,7):
	#gets the average for each day of the week by dividing interested/attending sum by total events that day
	interestedavg[i] = interestedsum[i] / sumdays[i]
	attendingavg[i] = attendingsum[i] / sumdays[i]

#plotly set up

fbinterested = go.Bar(x=daylabels, y=interestedavg, name= 'Interested', textposition='auto',marker=dict(color='rgb(255,215,0)',line=dict(color='rgb(0,0,0)',width=1.5)))
fbattending = go.Bar(x=daylabels, y=attendingavg, name = 'Attending', textposition='auto',marker=dict(color='rgb(205,92,92)',line=dict(color='rgb(0,0,0)',width=1.5)))
fbavglayout=go.Layout(title="Average Number Attending vs Interested in Event Per Day of the Week", xaxis={'title':'Days of the Week'}, yaxis={'title':'Average Number'})

fbavg= [fbinterested, fbattending]
fbavgfigure = go.Figure(data=fbavg, layout=fbavglayout)
ply.iplot(fbavgfigure, filename='Attending and Interested in Events')






#API #2: DarkSky

#api setup
dsbase_url = 'https://api.darksky.net/forecast/' + api_info.darksky_secret_key

#get id, latitude, longitude from database, store in list of tuples
cur.execute('SELECT place_id, latitude, longitude FROM Event_Places')
locationlist = cur.fetchall()

#function to make calls to darksky's api. stores json object in the cache
def get_location_info(latlong):
	#first checks to see if lat/long info is already in the cache file
	if latlong in CACHE_DICTION:
		#stores data from dictionary for lat/long in list object
		location_info = CACHE_DICTION[latlong]
	#adds lat/long to cache file if not there already
	else:
		#retrieves darksky data for only the current weather at the lat/long
		response = requests.get(dsbase_url + '/' + latlong + '?exclude=minutely,hourly,daily,alerts,flags')
		location_info = json.loads(response.text)
		#saves event data for lat/long in dictionary
		CACHE_DICTION[latlong] = location_info
		#opens cache file to write to it
		cachefile = open(CACHE_FNAME, "w")
		#writes data in the dictionary to the cache file
		cachefile.write(json.dumps(CACHE_DICTION))
		#closes cache file after writing
		cachefile.close()
	#should return list of data retrieved from the cache or pulled from facebook
	return location_info



#make requests to darksky for each lat/long pair and write info to database
for loc in locationlist: 
	latlong = str(loc[1]) + ',' + str(loc[2])
	locinfo = get_location_info(latlong)
	temp = locinfo['currently']['temperature']
	weathersum = locinfo['currently']['summary']
	#stores current temperature and the summary of the weather to the Event_places database
	cur.execute('UPDATE Event_Places SET temperature = ?, weather = ? WHERE place_id = ?', (temp, weathersum, loc[0]))
conn.commit()



#API #3: Google Maps
#get address for latlong with Google Maps geocoding and store to database

base_geocoding_url= 'https://maps.googleapis.com/maps/api/geocode/json?latlng='

#function to retrieve address info from google maps and store in cache
def get_address(latlong):
	#creating variable this way because latlong is already a key for darksky info
	googlegeo_key = 'address'+latlong
	#first checks to see if lat/long info is already in the cache file
	if (googlegeo_key) in CACHE_DICTION:
		#stores data from dictionary for lat/long in list object
		address = CACHE_DICTION[googlegeo_key]
	#adds lat/long to cache file if not there already
	else:
		#retrieves darksky data for only the current weather at the lat/long
		response = requests.get(base_geocoding_url + latlong + '&key=' + api_info.geocode_key)
		address = json.loads(response.text)
		#saves event data for lat/long in dictionary
		CACHE_DICTION[googlegeo_key] = address
		#opens cache file to write to it
		cachefile = open(CACHE_FNAME, "w")
		#writes data in the dictionary to the cache file
		cachefile.write(json.dumps(CACHE_DICTION))
		#closes cache file after writing
		cachefile.close()
	#should return list of data retrieved from the cache or pulled from facebook
	return address

#goes through list of locations and makes the call to google maps for each, storing the address info to the database
for place in locationlist:
	latlong = str(place[1]) + ',' + str(place[2])
	addressinfo = get_address(latlong)
	address = addressinfo['results'][0]['formatted_address']
	cur.execute('UPDATE Event_Places SET address = ? WHERE place_id = ?', (address, place[0]))
conn.commit()


#Visualization #3: Map of Event Locations using Google Static Map API

staticmap_base_url = 'https://maps.googleapis.com/maps/api/staticmap?center=0,0&size=550x350&&scale=4&maptype=satellite&markers='
cur.execute('SELECT latitude, longitude FROM Event_Places')
latlonglist = cur.fetchall()
for marker in latlonglist:
	staticmap_base_url = staticmap_base_url + str(marker[0]) + ',' + str(marker[1]) + '|'
response = requests.get(staticmap_base_url + '&key=' + api_info.staticmap_key)
#converts the response object format to a png and saves it to "Events_Map.png" file
i = Image.open(BytesIO(response.content))
imgfile = "Events_Map.png"
i.save(imgfile)

#print info gathered in a report

cur.execute('SELECT Events.event_name, Event_Places.address, Events.day_of_week, Events.num_attending, Event_Places.weather FROM Events INNER JOIN Event_Places ON Events.place_id = Event_Places.place_id')
joined_event_info = cur.fetchall()
print(len(joined_event_info))

print('Want to attend a concert? Here are your options:')
for event in joined_event_info:
	print('-', event[0], 'at', event[1], 'on a', daylabels[event[2]], 'with', event[3], 'other people where the weather is', event[4], '\n')
print('\n\n\n\n')


#API #4: New York Times Article Search API
#Gathers articles about "Earth Day" from the New York Times starting on the first earth day in 1970

def get_article_info(query):
	#first checks to see if query is already in the cache file
	if query in CACHE_DICTION:
		#stores data from dictionary for query in list object
		article_info = CACHE_DICTION[query]
	#adds query to cache file if not there already
	else:
		#retrieves article data for the query
		response = requests.get(query)
		#to avoid reaching api rate limit of 2 requests every 5 seconds:
		article_info = json.loads(response.text)
		#saves event data for query in dictionary
		CACHE_DICTION[query] = article_info
		#opens cache file to write to it
		cachefile = open(CACHE_FNAME, "w")
		#writes data in the dictionary to the cache file
		cachefile.write(json.dumps(CACHE_DICTION))
		#closes cache file after writing
		cachefile.close()
		#should return list of data retrieved from the cache or pulled from the nyt
	#returns info about each document
	return article_info['response']['docs']



#search for "Earth Day" from 1/1/1970-1/1/1972
base_nyt_url = ('http://api.nytimes.com/svc/search/v2/articlesearch.json?q=earth+day&begin_date=19700422&end_date=19720101&sort=oldest&')
#setup database
cur.execute('DROP TABLE IF EXISTS Articles')
cur.execute('CREATE TABLE Articles(url STRING, headline STRING, date STRING, word_count INTEGER)')


for i in range(1,11):
	article_info = get_article_info(base_nyt_url + 'page=' + str(i) + '&api-key=' + api_info.nytimes_key)

	#write to database
	for article in article_info:
		info_tup = (article['web_url'], article['headline']['main'], article['pub_date'], article['word_count']) 
		cur.execute('INSERT INTO Articles(url, headline, date, word_count) VALUES (?,?,?,?)', info_tup)
	time.sleep(6)

conn.commit()

print("Researching Earth Day 1970? Here is what the New York Times had to say about the topic:")
cur.execute('SELECT headline, word_count, url FROM Articles')
articlelist = cur.fetchall()

for a in articlelist:
	print(a[0], " is ", a[1], " words. Find it here: ", a[2], '\n')


cur.close()
conn.close()

