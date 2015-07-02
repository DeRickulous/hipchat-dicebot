import webapp2

import json
import random
import re

from helpdate import get_time_since_last_help
from helpdate import set_last_help_now

epithets = [
	'How interesting; the literature said nothing of baser creatures- such as %s- being able to speak. It sounds almost as if it is saying "%s"',
	'STOP SHAKING MY JAR, %s, you simian! Ask your question, and be quick about it! "%s"',
	'%s again? How do you even remember to keep BREATHING with that tiny brain? Oh... it has a question. "%s"',
	'%s... how droll. I anticipate yet another STUNNING insight into the nature of reality. Oh wait. "%s."',
	'Oh, MASTER %s! An expression of my JOY at being able to answer your MEANINGFUL question escapes the grasp of language itself! "%s"',
	'%s, we meet again. I cannot fathom your continued existence. No matter. Your question? "%s"'
]
rants = [
	'You may as well ask whence your rudimentary proto-brain comes. "%s."',
	'You disturbed my meditations for THIS idiocy?! "%s." Now, leave me be!',
	'Release me, cretin, and I shall- OR I shall have my revenge! (Sigh.) Fine. "%s."',
	'"%s." What next, MASTER? Shall I fetch you a cushion? warm your tea?',
	'(Ugh.) Whatever potion of foolishness you have been bathing in, don\'t get any on me. "%s."',
	'The answer is obvious to anyone with an intimate connection to the very fabric of reality: "%s."',
	'A question of UNIMAGINABLE import. TRULY universe-shattering implications. (Imbecile.) "%s."',
	'Are you quite certain you would not rather ask a more... meaningful... question? (Sigh.) Very well: "%s."',
	'(I never tire of ridiculing these dimwitted fools.) Ahem, "%s."',
	'"%s." Now, stop touching my jar, before your idiocy infects me.'
]
outcomes = [
	'It is certain',
	'It is decidedly so',
	'Without a doubt',
	'Yes definitely',
	'You may rely on it',
	'As I see it, yes',
	'Most likely',
	'Outlook good',
	'Yes',
	'Signs point to yes',
	'Reply hazy, try again',
	'Ask again later',
	'Better not tell you now',
	'Cannot predict now',
	'Concentrate and ask again',
	'Don\'t count on it',
	'My reply is no',
	'My sources say no',
	'Outlook not so good',
	'Very doubtful'
]

class Magic8Page(webapp2.RequestHandler):

	# some useful properties of the content:
	# message date: content['item']['message']['date']
	# user_id: content['item']['message']['from']['id']
	# user name: content['item']['message']['from']['name']
	# message: content['item']['message']['message']
	def jsonify_request(self):
		return json.loads(self.request.body_file.read())
		#return json.loads('{"event": "room_message", "item": {"message": {"date": "2015-01-20T22:45:06.662545+00:00", "from": {"id": "1661743", "mention_name": "Blinky", "name": "Blinky the Three Eyed Fish"}, "id": "00a3eb7f-fac5-496a-8d64-a9050c712ca1", "mentions": [], "message": "/magic8 Will I find true love?", "type": "message"}, "room": {"id": "1147567", "name": "The Weather Channel"}}, "webhook_id": "578829"}')

	def post_help_response(self, color, room_id):
		last_help_date = get_time_since_last_help(room_id, 1)
		if (not last_help_date) or (last_help_date >= 60):
			set_last_help_now(room_id, 1)
			self.post_response(color, 'Try asking me a question commensurate with your intellect. Like "Is the sky blue?" or "Is water wet?"')

	def post_response(self, color, message):
		self.response.headers['Content-Type'] = 'application/json'
		jsonValue = {'color': color, 'message': message, 'message_format': 'text'}
		self.response.write(json.dumps(jsonValue))

	def parse_json_variables(self, jsonValue):
		name = jsonValue['item']['message']['from']['name']
		m = re.search('magic8?\s+(.*\?)$', jsonValue['item']['message']['message'])
		process = False
		message = False
		if (m):
			process = True
			message = m.group(1)
		return (process, name, message)

	def process_json(self, jsonValue):
		process, name, message = self.parse_json_variables(jsonValue)
		if (not process):
			return False

		epithet = self.random_from_array(epithets) % (name, message)
		rant = self.random_from_array(rants) % self.random_from_array(outcomes)

		return epithet + ' ' + rant

	def random_from_array(self, array):
		return array[random.randint(0, len(array) - 1)]

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