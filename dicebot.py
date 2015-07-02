import webapp2

from roll import RollPage
from magic8 import Magic8Page

app = webapp2.WSGIApplication([
	('/', RollPage),
	('/magic8', Magic8Page),
], debug=True)