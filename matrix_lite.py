from time import time

from webrequests import *

def register(username, display_name=None, auth={}):
	if not display_name: display_name = username

	connect = request(c)
	connect.send('POST', '/client/r0/register', payload={'auth' : auth, 'username' : username})
	rcode, headers, payload = connect.recv()

	if rcode == 200:
		print('[INFO] Registration as "'+display_name+'" OK')
		connect = request(c)
		connect.send('PUT', '/client/r0/profile/@' + username + ':' + c['domain'] + '/displayname', payload={'displayname': display_name})

		rcode, headers, payload = connect.recv()
		return payload
	return payload

def room_create(name, alias=None, topic=None, public=False, federate=False, group_room=True):
	connect = request(c)

	if ' ' in alias: alias = alias.replace(' ', '')

	data = {'preset' : 'public_chat' if group_room else 'private_chat', # User or Group chat?
		'join_rule' : 'public' if public else 'invite',
		'room_alias_name' : alias if alias else name,
		'name' : name,
		'topic' : topic if topic else '',
		'creations_content' : {
			'm.federate' : 'true' if federate else 'false'
		}}

	connect.send('POST', '/client/r0/createRoom', data)
	resp_code, headers, payload = connect.recv()

	return payload

def room_join(room):
	connect = request(c)

	connect.send('POST', '/client/r0/rooms/' + room + '/join')
	resp_code, headers, payload = connect.recv()

	return payload

def room_invite(room, user):
	connect = request(c)

	connect.send('POST', '/client/r0/rooms/' + room + '/invite', {'user_id' : user})
	resp_code, headers, payload = connect.recv()

	return payload

def room_getId(alias):
	connect = request(c)

	connect.send('GET', '/client/r0/directory/room/#' + alias + ':' + c['domain'])
	resp_code, headers, payload = connect.recv()

	return payload

def room_getAlias(room_id):
	if ':' in room_id: room_id, domain = room_id.split(':', 1)
	connect = request(c)

	connect.send('GET', '/client/r0/rooms/{}/state/m.room.canonical_alias'.format(room_id + ':' + c['domain']))
	resp_code, headers, payload = connect.recv()

	#print(resp_code, headers, payload)
	# TODO: Might fail, some rooms don't have an alias? if so, use m.room.name instead (arbitrary tho)
	return payload['alias']

def room_mode(room, mode):
	#PUT /client/r0/directory/list/appservice/test.domain.com/!lEsjTTtbVuKfpEhxtT%3Amatrix.domain.com
	payload = {"visibility":"public"}

def room_usermod(room, user, admin=False):
	# TODO: Actual user modifications haha.
	connect = request(c)

	levels = {"users":{
			'@anton:matrix.org' : 100,
			'@twilio:matrix.org' : 100
			},
		"state_default" : "50",
		"kick" : "50",
		"ban" : "50",
		"redact" : "50",
		"events_default" : "0",
		"users_default" : "0",
		"events" : {"m.room.power_levels" : "100", "m.room.name" : "100"}}


	connect.send('PUT', '/client/r0/rooms/' + room + '/state/m.room.power_levels', levels)
	resp_code, headers, payload = connect.recv()

	return payload

def room_leave(room):
	connect = request(c)

	connect.send('POST', '/client/r0/rooms/' + room + '/leave')

	resp_code, headers, payload = connect.recv()
	return payload

def send_encrypted(room, message, user_id={}, formatted_message={}):
	if ':' in room: room, domain = room.split(':', 1)

	#data = {'age': 56
	#	ontent: {'algorithm': 'm.megolm.v1.aes-sha2', 'ciphertext': 'AwgnGTakxULc+nEqGLnDGSc0Ww/dbf5NfLHuyQH', 'device_id': 'NNQQAEFDDJ', 'sender_key': 'wKDR3uJ2PBnRjZjeY6fjemy5FHCCu4wd1lK9QEseBc', 'session_id': 'sbv1oL2EnJq2+jxP7wDcOfmcsVSbMyuDw78jImqNuHI'}
	#	event_id: $14888258521308GjLIg:matrix.org
	#	origin_server_ts: 1488825852325
	#	room_id: !rzQieMvDdkBkSAeHtj:matrix.org
	#	sender: @anton:matrix.org
	#	type: m.room.encrypted
	#	unsigned: {'age': 56}
	#	user_id: @anton:matrix.org
	#}

	enc_msg = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
	bencoded = b64encode(enc_msg.encrypt(message))

	data = {'algorithm' : 'm.megolm.v1.aes-sha2',
		'ciphertext' : bencoded,
		'sender_key' : 'wKbR3uJ2P7nRjZj8DY6fjLmy5FHCCu4wd1lK9QEseBc',
		'device_id' : 'NNKQAEFDDJ'}

	connect = request(c)

	if type(user_id) != dict:
                user_id = {'user_id' : user_id}

	connect.send('PUT', '/client/r0/rooms/'+room+':'+c['domain']+'/send/m.room.encrypted/m'+str(time()), data, user_id)

	resp_code, headers, payload = connect.recv()
	print(resp_code, headers, payload)
	return payload

def send(room, message, user_id={}, formatted_message={}):
	if ':' in room: room, domain = room.split(':', 1)
	connect = request(c)

	if type(user_id) != dict:
		user_id = {'user_id' : user_id}

	connect.send('PUT', '/client/r0/rooms/'+room+':'+c['domain']+'/send/m.room.message/m'+str(time()), {"msgtype":"m.text","body": message, "format": "org.matrix.custom.html", "formatted_body" : formatted_message}, user_id)
	resp_code, headers, payload = connect.recv()

	# Prior to returning the response payload.
	# We'll mute our own message so we don't have to listen to what we've already sent out.
	if 'event_id' in payload:
		mute_future_eventId(payload['event_id'])

	return payload

def join(room, user_id={}):
	if ':' in room: room, domain = room.split(':', 1)
	connect = request(c)

	if type(user_id) != dict:
		user_id = {'user_id' : user_id}

		connect.send('POST', '/client/r0/join/'+room+':'+c['domain'], {}, user_id)

	resp_code, headers, payload = connect.recv()
	return payload
