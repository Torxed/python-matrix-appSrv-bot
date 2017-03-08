from threading import *
from time import time, sleep

from matrix_lite import *

def parse_invites(event):
	if event['membership'] == 'invite':
			join(event['room_id'])

class invites_checker():
	def __init__(self):

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
		register_event_hook('membership', __name__, parse_invites)

c['plugins'][__name__] = {'main_function' : invites_checker, 'parameters' : {}}