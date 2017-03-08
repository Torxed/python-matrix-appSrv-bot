import imp, importlib.machinery
from glob import glob
from sys import exit
from os.path import basename, abspath, dirname, isfile, isdir, exists
from socket import *
from json import dumps, loads
from threading import *
from time import sleep
from collections import OrderedDict

## == Handle Ctrl+C signal:
import signal
alive = True
def signal_handler(signal, frame):
	print('[CORE] Shutting down...')
	for t in enumerate():
		if t.name != 'MainThread':
			t.kill()

	alive=False
	active_count = 0
	while len(enumerate()) > 1 and active_count < 10: # 10 second grace
		sleep(1)
		active_count += 1

	
	for t in enumerate():
		if t.name != 'MainThread':
			t._stop()

	exit(0) # Last resort.
signal.signal(signal.SIGINT, signal_handler)
## -----

## Custom libraries:
from config import *
from matrix_lite import *

## == I strongly suggest I myself use the SDK instead (probably): https://github.com/matrix-org/matrix-python-sdk
##    I just tend to like doing things manually, teaches me more about the protocol etc.

# https://github.com/matrix-org/synapse/blob/master/synapse/handlers/profile.py
# https://matrix.org/blog/2015/03/02/introduction-to-application-services/
# https://matrix.org/docs/api/client-server/
# http://matrix.org/docs/spec/client_server/r0.2.0.html#sending-events-to-a-room
# http://matrix.org/docs/spec/client_server/r0.2.0.html#m-room-power-levels
# https://matrix.org/jira/si/jira.issueviews:issue-html/SYN-351/SYN-351.html

c['events_parsed'] = OrderedDict() # TODO: Only used because I haven't figured out a proper response to events yet.

def load_module(m):
	print('[CORE] Loading plugins:', m)
	if isfile('./plugins/'+ m +'.py'):
		namespace = m.replace('/', '_').strip('\\/;,. ')
		#print('    Emulating ElasticSearch via script:',namespace,fullPath.decode('utf-8')+'.py')
		loader = importlib.machinery.SourceFileLoader(namespace, abspath('./plugins/'+ m +'.py'))
		handle = loader.load_module(namespace)
		# imp.reload(handle) # Gotta figure out how this works in Py3.5+
		#ret = handle.main(request=request)
		load_count = 0
		while m not in c['plugins'] and load_count < 3:
			sleep(0.2)

		if m in c['plugins']:
			x = c['plugins'][m]['main_function'](**c['plugins'][m]['parameters'])
			if hasattr(x, 'setName'):
				x.setName(m)
			print('[SUCCESS] Module activated.')
		else:
			print('[ERROR] Could not load this module.')

def mute_future_eventId(event_id):
	# Enables features like matrix_lite.send() to mute
	# The outbound messages it sends, so that when the server
	# sends us the event later on, we've already muted it.
	c['events_parsed'][event_id] = True

def register_event_hook(context, module, function, exclusive=False):
	if not context in c['event_hooks']:
		c['event_hooks'][context] = {}
	if not module in c['event_hooks'][context]:
		c['event_hooks'][context] = {}

	c['event_hooks'][context][module] = {'function' : function, 'exclusive' : exclusive}
## Register the event_hook() and mute_event() functions as globally accessible functions
## (So that submodules and threads can use it easily, makes for one less .py file that plugins need to import)
__builtins__.__dict__['register_event_hook'] = register_event_hook
__builtins__.__dict__['mute_future_eventId'] = mute_future_eventId

def parse_API_events(headers, data, s):
	"""
	Example event:

	{'membership': 'invite'}
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
	"""
	if 'events' in data:
		for event in data['events']:
			parsed = False
			#print(event)
			if 'event_id' in event:
				if event['event_id'] not in c['events_parsed']:
					mute_future_eventId(event['event_id'])
					#events_parsed[event['event_id']] = True
				else:
					print('[INFO] Muting duplicate event') # (Because we have yet not implemented the correct reply for previous events)
					continue

			if 'content' in event:
				for event_key in event['content'].keys():
					if event_key in c['event_hooks']:
						for parser, parser_meta in c['event_hooks'][event_key].items():
							ret_code = parser_meta['function'](event)
							if ret_code:
								parsed = True
							
							if parser_meta['exclusive']:
								print('[INFO]',parser,'has exclusive rights to events:',event['content'].keys())
								
								if not ret_code:
									print('[ERROR]',parser,'could not parse [exclusive] event:', event)
								
								continue # Will jump to the next event.

							#c['event_hooks']['msgtype']['sms_twilio'] = {'function' : x, 'exclusive' : False}

					elif event_key == 'membership' and event['content']['membership'] == 'join': continue

					elif event_key == 'membership' and event['content']['membership'] == 'invite' and 'state_key' in event and event['state_key'] == '@'+c['user']+':'+c['domain']:
							print('[INFO] Got invited to:', event['room_id'], '- Politely accepting it!')
							room_join(event['room_id'])
							parsed = True

			if not parsed:
				print('[INFO] No registered hook for event:')
				for key, val in event.items():
					print('  ' + str(key) + ': ' + str(val))
			#for key, val in event.items():
			#	print('  ' + str(key) + ': ' + str(val))

		## We always reply with a "OK" message, for now.
		## This is absoluteley not the correct implementation, but it gets us off the hook for playing around some more.
		s.send(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}')

class API_Reciever(Thread):
	def __init__(self):
		Thread.__init__(self)

		print('[API] Listening for API events from Matrix')
		self.s = socket()
		self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.s.bind((c['callbacks'], c['callback_port']))
		self.s.listen(4)

		self.alive = True
		self.start()

	def kill(self):
		self.alive = False
		self.s.close()

		## This should release our self.s.accept() lock in the running thread.
		s = socket()
		s.connect((c['callbacks'], c['callback_port']))
		s.close()

	def run(self):
		main = None
		for t in enumerate():
			if t.name == 'MainThread':
				main = t
				break

		while self.alive and main and main.isAlive():
			ns, na = self.s.accept()

			data = ns.recv(8192)

			if not b'\r\n\r\n' in data:
				print('[INFO] Malicious data sent to API_Reciever()')
				ns.close()
				continue

			header, data = data.split(b'\r\n\r\n',1)
			request, header = header.split(b'\r\n',1)

			headers = {}
			for obj in header.split(b'\r\n'):
				if b': ' in obj:
					key, val = obj.split(b': ',1)
					headers[key.strip().lower()] = val.strip()

			headers['request'] = request
			try:
				jdata = loads(data)
			except:
				print('[API] Could not decode JSON data:', str([header]), str([data]))
				#ns.send(b'HTTP/1.1 404 Not Found\r\nDate: Sat, 04 Mar 2017 19:58:38 GMT\r\nConnection: close\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: 153\r\nServer: TwistedWeb/16.6.0\r\n\r\n\n<html>\n  <head><title>404 - No Such Resource</title></head>\n  <body>\n    <h1>No Such Resource</h1>\n    <p>No such child resource.</p>\n  </body>\n</html>\n')
				ns.close()
				continue

			parse_API_events(headers, jdata, ns)
			ns.close()


## First, we register ourselves with the server.
## We will supply a username for ourselves and join a channel if we so wish.
register(c['user'], display_name='Twilio SMS')
if c['main_room']:
	join(c['main_room'], '@'+c['user']+':'+c['domain'])

## Then, we load any plugins outside of the normal !cmd syntax.
## - Normal !cmd syntax will be found in the parse_API_events() function.
##
## (And, of course event driven bot logic, invites etc for instance)
for file in glob('./plugins/*.py'):
	load_module(basename(file).split('.')[0])

## Here's some example commands we can use:
#room_leave('!YeYXpnmErDOAgnojeU:matrix.org')
#room_leave('!towPteNqZmNNOWTEgy:matrix.org')
#room_usermod('!towPteNqZmNNOWTEgy:matrix.org', '@anton:matrix.org', admin=True)
#room_usermod('!YeYXpnmErDOAgnojeU:matrix.org', '@anton:matrix.org', admin=True)
#room_create('Testing private room 2', alias='mail_anton.doxid@gmail.com', public=True, group_room=False)
#room_invite('!ECWjnfGJuPjMaGgFui:matrix.org', '@anton:matrix.org')
#ret = room_create('Anton Hvornum', alias='mail_anton.doxid@gmail.com', group_room=False)
#if ret['error'] == 'Room alias already taken':
#	print(room_getId(alias='mail_anton.doxid@gmail.com'))

## WIP:
#send_encrypted('!rzQieMvgdkGkSAeHtj:matrix.org', 'This should be encrypted!', '@'+ c['user'] +':'+ c['domain'])

API_Reciever()

while 1:
	sleep(0.25)

bg.kill()
