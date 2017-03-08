from threading import *
from time import time, sleep

from matrix_lite import *

class invites_checker(Thread):
	def __init__(self):
		Thread.__init__(self)

		""" Example event:
		{
		  age: 74
		  content: {'membership': 'invite'}
		  event_id: $1488724865147CcSnH:domain.com
		  membership: invite
		  origin_server_ts: 1488724865910
		  room_id: !AShvPqYHtSJhfoaPzf:domain.com
		  sender: @anton:domain.com
		  state_key: @twilio:domain.com
		  type: m.room.member
		  unsigned: {'age': 74}
		  user_id: @anton:domain.com
		}
		"""

		## This will enable us to retrieve any invite/join/kick events.
		## (Because the event hook witll look in 'content' for keys.)
		register_event_hook('membership', __name__, self.parse)

		self.alive = True
		self.start()

	def parse(self, event):
		if event['membership'] == 'invite':
			join(event['room_id'])

	def kill(self):
		self.alive = False

	def run(self):
		main = None
		for t in enumerate():
			if t.name == 'MainThread':
				main = t
				break

		last_run = time()-10
		while self.alive and main and main.isAlive():
			## This time checker is instead of sleep()
			## (It enables us to shut down quicker)
			if time() - last_run < 10:
				sleep(0.25); continue
			last_run = time()

			## This is where you'd do your continous/blocking calls.
			## see ./examples/non_threaded_plugin.py for another xample.

c['plugins'][__name__] = {'main_function' : invites_checker, 'parameters' : {}}