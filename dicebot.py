import webapp2
import json
import random
import math
import re

class MainPage(webapp2.RequestHandler):
	# some useful properties of the content:
	# message date: content['item']['message']['date']
	# user_id: content['item']['message']['from']['id']
	# user name: content['item']['message']['from']['name']
	# message: content['item']['message']['message']
	def jsonify_request(self):
		return json.loads(self.request.body_file.read())
		#return json.loads('{"event": "room_message", "item": {"message": {"date": "2015-01-20T22:45:06.662545+00:00", "from": {"id": "1661743", "mention_name": "Blinky", "name": "Blinky the Three Eyed Fish"}, "id": "00a3eb7f-fac5-496a-8d64-a9050c712ca1", "mentions": [], "message": "roll top 1 of 2d20 +1 to save versus death", "type": "message"}, "room": {"id": "1147567", "name": "The Weather Channel"}}, "webhook_id": "578829"}')

	def post_response(self, color, message):
		self.response.headers['Content-Type'] = 'application/json'
		self.response.write('{"color": "%s", "message": "%s", "message_format": "text"}' % (color, message));

	def parse_json_variables(self, json):
		name = json['item']['message']['from']['name']
		m = re.search('rolls?\s+(?:(max|top|min|bot|bottom)\s*(\d+)\s*of\s*)?(\d+)\s*d\s*(\d+)(?:\s*(\+|\-)\s*(\d+))?(?:\s+(.*))?$', json['item']['message']['message'])
		keep_top = False
		keep = 0;
		count = 0
		die_size = 0
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
			if (m.group(6)):
				modifier = int(m.group(6))
			if (m.group(5)) == '-':
				modifier = 0 - modifier
			if (m.group(7)):
				message = m.group(7)
		return (process, keep_top, keep, count, die_size, modifier, name, message)

	def process_json(self, json):
		process, keep_top, keep, count, die_size, modifier, name, message = self.parse_json_variables(json)
		if (not process):
			return False
		if (keep and keep_top):
			keep_string = ' top %i of' % keep
		elif (keep):
			keep_string = ' bottom %i of' % keep
		else:
			keep_string = ''
		if (count <= 0):
			return '%s tries to roll zero dice, but just ends up looking silly.' % name
		if (die_size <= 0):
			return '%s tries to roll zero-sided dice, but they never stop rolling...' % name
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
			

		total, results = self.roll_dice2(keep, keep_top, count, die_size)
		total = total + modifier

		return '%s rolls%s:%s %id%i [%s]%s = %i' % (name, message, keep_string, count, die_size, results, modifier_string, total)

	# returns a tuple in the form: (12, '4, 1, 5, 2')
	def roll_dice(self, keep, keep_top, count, die_size):
		results = ''
		total = 0
		for i in range(0, count):
			result = random.randint(1, die_size)
			total = total + result
			if (i < 20 or count <= 25):
				if i > 0:
					results = results + ', '
				results = results + str(result)
		if count > 25:
			results = results + ' and %i more...' % (count - 20)
		return (total, results)

	def roll_dice2(self, keep, keep_top, count, die_size):
		results = [None] * count
		total = 0
		for i in range(0, count):
			result = random.randint(1, die_size)
			results[i] = [i, result, False]
			total = total + result
		if (keep_top):
			results = sorted(results, key=lambda x: (0 - x[1]))
		else:
			results = sorted(results, key=lambda x: x[1])
		if (keep):
			total = 0
			for i in range(0, keep):
				results[i][2] = True
				total = total + results[i][1]
			results = sorted(results, key=lambda x: x[0])
		result_string = ''
		if (count <= 25):
			loop_max = count
		else:
			loop_max = 20
		for i in range(0, loop_max):
			if (i > 0):
				result_string = result_string + ', '
			result_string = result_string + str(results[i][1])
			if (results[i][2] and keep):
				result_string = result_string + '*'
		if (count > 25):
			result_string = result_string + ' and %i more...' % (count - 20)
		return (total, result_string)

	def post(self):
		json = self.jsonify_request()
		message = self.process_json(json)
		if (message):
			self.post_response('green', message)

	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		self.response.write('<form method="POST"><input type="text" name="x"></input><input type="submit"></input></form>');

app = webapp2.WSGIApplication([
	('/', MainPage),
], debug=True)