import webapp2

from google.appengine.ext import ndb
from helpdate import get_time_since_last_help
from helpdate import set_last_help_now

import json
import random
import math
import re
import time

class RollPage(webapp2.RequestHandler):

	# some useful properties of the content:
	# message date: content['item']['message']['date']
	# user_id: content['item']['message']['from']['id']
	# user name: content['item']['message']['from']['name']
	# message: content['item']['message']['message']
	def jsonify_request(self):
		return json.loads(self.request.body_file.read())
		#return json.loads('{"event": "room_message", "item": {"message": {"date": "2015-01-20T22:45:06.662545+00:00", "from": {"id": "1661743", "mention_name": "Blinky", "name": "Blinky the Three Eyed Fish"}, "id": "00a3eb7f-fac5-496a-8d64-a9050c712ca1", "mentions": [], "message": "/roll 10d6", "type": "message"}, "room": {"id": "1147567", "name": "The Weather Channel"}}, "webhook_id": "578829"}')

	def post_help_response(self, color, room_id):
		last_help_date = get_time_since_last_help(room_id, 0)
		if (not last_help_date) or (last_help_date >= 60):
			set_last_help_now(room_id, 0)
			self.post_response(color, '''Usage: /roll {keep} {m}d{n} {explode} {bonus} {message}
			   m: number of dice to roll
			   n: number of sides per die
			   keep: throws away a number of dice ('top # of', 'bot # of', 'bottom # of') [optional]
			   explode: a certain number of (or all) dice may "explode" ('x', 'x#') [optional]
			   bonus: add or subtract a bonus to the final roll ('+#', '-#') [optional]
			   message: apply a certain text message to the roll response [optional]
			(This help response will only display every 60 seconds.)''')

	def post_response(self, color, message):
		self.response.headers['Content-Type'] = 'application/json'
		jsonValue = {'color': color, 'message': message, 'message_format': 'text'}
		self.response.write(json.dumps(jsonValue))

	def parse_json_variables(self, jsonValue):
		name = jsonValue['item']['message']['from']['name']
		m = re.search('rolls?\s+(?:(max|top|min|bot|bottom)\s*(\d+)\s*of\s*)?(\d+)\s*d\s*(\d+)(?:\s*x(\d*))?(?:\s*(\+|\-)\s*(\d+))?(?:\s*(.*))?$', jsonValue['item']['message']['message'])
		keep_top = False
		keep = 0;
		count = 0
		die_size = 0
		explode_count = 0
		modifier = 0
		message = False
		process = False
		if (m):
			process = True
			if (m.group(1) == 'top' or m.group(1) == 'max'):
				keep_top = True
			if (m.group(2)):
				keep = int(m.group(2))
			if (m.group(3)):
				count = int(m.group(3))
			if (m.group(4)):
				die_size = int(m.group(4))
			if (m.group(5) == ''):
				explode_count = count
			elif (m.group(5)):
				explode_count = min(count, int(m.group(5)));
			if (m.group(7)):
				modifier = int(m.group(7))
			if (m.group(6)) == '-':
				modifier = 0 - modifier
			if (m.group(8)):
				message = m.group(8)
		return (process, keep_top, keep, count, die_size, explode_count, modifier, name, message)

	def process_json(self, jsonValue):
		process, keep_top, keep, count, die_size, explode_count, modifier, name, message = self.parse_json_variables(jsonValue)
		if (not process):
			return False
		if (keep and keep_top):
			keep_string = ' top %i of' % keep
		elif (keep):
			keep_string = ' bottom %i of' % keep
		else:
			keep = count
			keep_string = ''
		if (count <= 0):
			return '%s tries to roll zero dice, but just ends up looking silly.' % name
		if (die_size <= 0):
			return '%s tries to roll zero-sided dice, but they never stop rolling...' % name
		elif (die_size == 1):
			explode_count = 0
		if (modifier > 0):
			modifier_string = ' + %i' % modifier
		elif (modifier < 0):
			modifier_string = ' - %i' % abs(modifier)
		else:
			modifier_string = ''
		if (message):
			message = ' ' + message
		else:
			message = ''
		if (explode_count > 0):
			explode_string = ' (%i exploding)' % explode_count
		else:
			explode_string = ''

		total, results = self.roll_dice(keep, keep_top, count, explode_count, die_size)
		total = total + modifier

		return '%s rolls%s:%s %id%i [%s]%s%s = %i' % (name, message, keep_string, count, die_size, results, explode_string, modifier_string, total)

	# returns a tuple in the form: (12, '4, 1, 5, 2')
	def roll_dice(self, keep, keep_top, count, explode_count, die_size):
		results = []
		for i in range(0, count):
			results.append([i, self.roll_die(die_size, i < explode_count), False])
		# sort the list by the total of the result array
		sum = lambda x, y: x + y
		if (keep_top):
			results = sorted(results, key=lambda x: (0 - reduce(sum, x[1])))
		else:
			results = sorted(results, key=lambda x: reduce(sum, x[1]))
		# iterate over the first [keep] records of the list, simultaneously flagging (third element of subarray) and summing (second element of subarray)
		total = 0
		for i in range(0, keep):
			results[i][2] = True
			total = total + reduce(sum, results[i][1])
		# return the array to its original order
		results = sorted(results, key=lambda x: x[0])
		# construct the result string
		result_string = ''
		if (count <= 25):
			loop_max = count
		else:
			loop_max = 20
		# iterate over the results (all of them, or only 20 if there are more than 25)
		for i in range(0, loop_max):
			if (i > 0):
				result_string = result_string + ', '
			if (len(results[i][1]) == 1):
				result_string = result_string + str(results[i][1][0])
			else:
				result_string = result_string + str(results[i][1])
			if (results[i][2] and (keep < count)):
				result_string = result_string + '*'
		if (count > 25):
			result_string = result_string + ' and %i more...' % (count - 20)
		return (total, result_string)

	def roll_die(self, die_size, explode):
		results = []
		while ((len(results) == 0) or (explode and (results[len(results) - 1] == die_size))):
			results.append(random.randint(1, die_size))
		return results

	def post(self):
		jsonValue = self.jsonify_request()
		message = self.process_json(jsonValue)
		if (message):
			self.post_response('gray', message)
		else:
			self.post_help_response('gray', str(jsonValue['item']['room']['id']))

	#def get(self):
	#	self.response.headers['Content-Type'] = 'text/html'
	#	self.response.write('<form method="POST"><input type="text" name="x"></input><input type="submit"></input></form>');