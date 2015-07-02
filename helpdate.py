from google.appengine.ext import ndb

import time

class HelpDateStore(ndb.Model):
	room_id = ndb.StringProperty()
	help_type = ndb.IntegerProperty()
	time = ndb.IntegerProperty(indexed=False)

def get_time_since_last_help(room_id, help_type):
	now = int(time.time())
	last_help_dates = HelpDateStore.query(HelpDateStore.room_id==room_id, HelpDateStore.help_type==help_type).fetch(1)
	for last_help_date in last_help_dates:
		return now - last_help_date.time
	return False

def set_last_help_now(room_id, help_type):
	last_help_dates = HelpDateStore.query(HelpDateStore.room_id==room_id, HelpDateStore.help_type==help_type).fetch(1)
	for last_help_date in last_help_dates:
		last_help_date.time = int(time.time())
		last_help_date.put()
		return
	last_help_date = HelpDateStore()
	last_help_date.room_id = room_id
	last_help_date.help_type = help_type
	last_help_date.time = int(time.time())
	last_help_date.put()