import imaplib
import datetime
import email
import smtplib
from email.mime.text import MIMEText
from threading import *
from time import time, sleep

from matrix_lite import *

notified_mails = {}

class mail(Thread):
	def __init__(self):
		Thread.__init__(self)

		self.mail = None
		register_event_hook('msgtype', __name__, self.parse)

		self.alive = True
		self.start()

		#result, data = mail.uid('search', None, "ALL") # search and return

	def parse(self, event):
		if event['content']['body'][:5] == 'mail:':
			cmd, to, msg = event['content']['body'].split(' ', 2)
			if event['sender'] in c['misc']['allowed_users']:

				if '[' in msg and ']' in msg:
					subj, msg = msg.split(']', 1)
					subj = subj.strip('[] \\.')
					msg = msg.strip('[] \\.')
				elif msg.count('.') >= 1 and len(msg[:msg.find('.')]) > 0 and len(msg[msg.find('.'):]) > 0:
					subj, msg = msg.split('.', 1)
				else:
					subj = 'Mail without subject.'

				msg = MIMEText(msg)
				msg['Subject'] = subj
				msg['From'] = c['gmail']['username']
				msg['To'] = to

				server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
				server.ehlo()
				#server.starttls() # Not required for SMTP_SSL

				server.login(c['gmail']['username'], c['gmail']['password'])
				server.sendmail(c['gmail']['username'], [to], msg.as_string())
				server.close()

				print('[Matrix]->[MAIL] Sent mail to:', to)
			else:
				if c['main_room']:
					send(c['main_room'], 'You\'re not allowed to send e-mails.', '@'+c['user']+':'+c['domain'])

			return True

	def login(self):
		self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
		self.mail.login(c['gmail']['username'], c['gmail']['password'])
		self.mail.list()
		# Out: list of "folders" aka labels in gmail.
		#mail.select('"[Gmail]/All Mail"') # connect to inbox. #or "inbox"
		self.mail.select("Inbox")

	def kill(self):
		self.alive = False

	def run(self):

		main = None
		for t in enumerate():
			if t.name == 'MainThread':
				main = t
				break

		join(c['gmail']['mail_room'], '@'+c['user']+':'+c['domain'])

		last_run = time()-10
		while self.alive and main and main.isAlive():
			## This time checker is instead of sleep()
			## (It enables us to shut down quicker)
			if time() - last_run < 10:
				sleep(0.25); continue
			last_run = time()

			if not self.mail:
				self.login()

			date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
			result, data = self.mail.uid('search', None, '(SENTSINCE {date})'.format(date=date))

			#for uid in reversed(data[0].split(b' ')):
			for uid in data[0].split(b' '):
				uid = uid.decode('UTF-8')

				if int(uid) in notified_mails: continue

				notified_mails[int(uid)] = True

				#result, raw_mail = mail.uid('fetch', uid.decode('UTF-8'), '(RFC822)')
				#result, raw_mail = mail.uid('fetch', uid.decode('UTF-8'), '(BODY[HEADER.FIELDS (DATE SUBJECT)]])')
				result, raw_mail = self.mail.uid('fetch', uid, '(BODY.PEEK[HEADER])')
				email_message = email.message_from_string(raw_mail[0][1].decode('UTF-8'))

				_from, msg = email_message['From'], email_message['Subject']
				mail_addr = _from
				if '<' in _from:
					_from, mail_addr = _from.split('<',1)
					mail_addr = mail_addr.strip('<> \\.;,')
				_from, msg = _from.strip('\r\n \\;"\''), msg.strip('\r\n \\;"\'')
				if len(msg) >= 70:
					msg = msg[:67]+'...'
				if '?' in _from:
					msg = str(email.header.make_header(email.header.decode_header(_from)))
				if '?' in msg:
					msg = str(email.header.make_header(email.header.decode_header(msg)))


				room_data = room_create(_from, alias='mail_' + mail_addr, group_room=False)
				if 'error' in room_data:
					if room_data['error'] == 'Room alias already taken':
						room_data = room_getId(alias='mail_' + mail_addr)
					else:
						print('[MAIL]->[Matrix] Delivering mail', uid,'to',c['main_room'])
						send(room_data['room_id'], 'New mail from "' + str(_from) + '"\n  - Subject: ' + str(msg), '@'+c['user']+':'+c['domain'],
						       formatted_message='<b>New mail from</b>: "' + str(_from) + '"\n <ul><li>Subject: ' + str(msg) + '</li></ul>')
						continue

				print('[MAIL]->[Matrix] Delivering mail', uid,'to', room_getAlias(room_data['room_id']))

				for admin in c['misc']['allowed_users']:
					#TODO: Create some sort of access list instead of allowing all admins to read each others messages haha.
					room_invite(room_data['room_id'], admin)
					room_usermod(room_data['room_id'], admin, admin=True)

				#send(c['gmail']['mail_room'], 'New mail from "' + str(_from) + '"\n  - Subject: ' + str(msg), '@'+c['user']+':'+c['domain'],
				#	formatted_message='<b>New mail from</b>: "' + str(_from) + '"\n <ul><li>Subject: ' + str(msg) + '</li></ul>')
				send(room_data['room_id'], 'New mail from "' + str(_from) + '"\n  - Subject: ' + str(msg), '@'+c['user']+':'+c['domain'],
					formatted_message='<b>New mail from</b>: "' + str(_from) + '"\n <ul><li>Subject: ' + str(msg) + '</li></ul>')

				if email_message['From'] is None: # or email_message['Subject'] is None:
					print('[MAIL]->[Matrix]  (Bad email)')
					for key, val in email_message.items():
						print('  ',key, '=', val)
				#print()

			self.mail.close()
			self.mail = None

c['plugins'][__name__] = {'main_function' : mail, 'parameters' : {}}