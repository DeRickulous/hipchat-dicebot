import webapp2
import logging

import json
import random
import math
import re
import time

class RollPage(webapp2.RequestHandler):

	def post_help_response(self):
		self.post_response('''Usage: /roll {keep} {m}d{n} {explode} {bonus} {message}
		   m: number of dice to roll
		   n: number of sides per die
		   keep: throws away a number of dice ('top # of', 'bot # of', 'bottom # of') [optional]
		   explode: a certain number of (or all) dice may "explode" ('x', 'x#') [optional]
		   bonus: add or subtract a bonus to the final roll ('+#', '-#') [optional]
		   message: apply a certain text message to the roll response [optional]''', False)

	def post_response(self, message, in_channel):
		self.response.headers['Content-Type'] = 'application/json'
		if (in_channel):
			jsonValue = {'response_type': 'in_channel', 'text': message}
		else:
			jsonValue = {'response_type': 'ephemeral', 'text': message}
		self.response.write(json.dumps(jsonValue))

	def parse_variables(self):
		name = self.request.get('user_name')
		logging.info(self.request.get('text'))
		m = re.search('\s*(?:(max|top|min|bot|bottom)\s*(\d+)\s*of\s*)?(\d+)\s*d\s*(\d+)(?:\s*x(\d*))?(?:\s*(\+|\-)\s*(\d+))?(?:\s*(.*))?$', self.request.get('text'))
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

	def process_request(self):
		process, keep_top, keep, count, die_size, explode_count, modifier, name, message = self.parse_variables()
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
			return '@%s tries to roll zero dice, but just ends up looking silly.' % name
		if (die_size <= 0):
			return '@%s tries to roll zero-sided dice, but they never stop rolling...' % name
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

		if (total.is_integer()):
			total = int(total)
		return '@%s rolls%s:%s %id%i [%s]%s%s = %s' % (name, message, keep_string, count, die_size, results, explode_string, modifier_string, str(total))

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
		total = 0.0
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
		message = self.process_request()
		if (message):
			logging.info(message)
			self.post_response(message, True)
		else:
			self.post_help_response()
		

	#def get(self):
	#	self.response.headers['Content-Type'] = 'text/html'
	#	self.response.write('<form method="POST"><input type="text" name="channel_id"></input><input type="text" name="text"></input><input type="submit"></input></form>');