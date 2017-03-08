from threading import *
from hashlib import sha256
from time import time, sleep

# Download the twilio-python library from http://twilio.com/docs/libraries
from twilio.rest import TwilioRestClient
#from matrix_light import room_name(id)

from matrix_lite import *

notified_mails = {}

class sms(Thread):
	def __init__(self):
		Thread.__init__(self)

		# Find these values at https://twilio.com/user/account
		#self.from_nr = c['twilio']['from']
		self.client = TwilioRestClient(c['twilio']['as'], c['twilio']['at'])

		register_event_hook('msgtype', __name__, self.parse)

		#message = client.messages.create(to=sys.argv[1], from_=from_nr, body=sys.argv[2])

		self.alive = True
		self.start()

	def parse(self, event):
		msg_body = event['content']['body']

		if msg_body[:4] == 'sms:':
			cmd, to, msg = msg_body.split(' ', 2)
			if event['sender'] in c['misc']['allowed_users']:
				
				account_sid = c['twilio']['as']
				auth_token = c['twilio']['at']
				client = TwilioRestClient(account_sid, auth_token)

				message = client.messages.create(to=to, from_=c['twilio']['from'], body=msg)
				print('[Matrix]->[SMS] SMS sent to:', to)
			else:
				if c['main_room']:
					send(c['main_room'], 'You\'re not allowed to send sms.', '@'+c['user']+':'+c['domain'])

			return True

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

			messages = self.client.messages.list(to=c['twilio']['from'])

			for message in messages:
				mhash = sha256(bytes(message.from_+message.body, 'UTF-8')).hexdigest()
				if mhash not in notified_mails:
					notified_mails[mhash] = True
				else:
					continue

				room_data = room_create(message.from_, alias='sms_' + message.from_, group_room=False)
				if 'error' in room_data:
					if room_data['error'] == 'Room alias already taken':
						room_data = room_getId(alias='sms_' + message.from_)
					else:
						print('[SMS]->[Matrix] Delivering sms from', message.from_, 'to', c['main_room'])
						send(room_data['room_id'], 'New sms from "' + str(message.from_) + '"\n  - ' + str(message.body), '@'+c['user']+':'+c['domain'],
						       formatted_message='<b>New sms from</b>: "' + str(message.from_) + '"\n <ul><li>' + str(message.body) + '</li></ul>')
						continue

				print('[SMS]->[Matrix]  Delivering sms from', message.from_, 'to', room_getAlias(room_data['room_id']))

				for admin in c['misc']['allowed_users']:
					#TODO: Create some sort of access list instead of allowing all admins to read each others messages haha.
					room_invite(room_data['room_id'], admin)
					room_usermod(room_data['room_id'], admin, admin=True)

				send(room_data['room_id'], str(message.from_) + ': ' + str(message.body), '@'+c['user']+':'+c['domain'],
					formatted_message='<b>' + str(message.from_) + '</b>: ' + str(message.body))

				#print(message.body)# /usr/bin/env python

c['plugins'][__name__] = {'main_function' : sms, 'parameters' : {}}