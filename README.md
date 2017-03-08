Why not SDK or twisted?
====

Learning experience and I don't like Twisted (Way to big for a simple task)
Other than that, there's no real reason not to use it. Might swap to it later on.

Configuration
====

Is done in `config.py`, most of it should be self explanatory.

How to run
=====

    python run.py

How to write more plugins
======

Use the template in `./examples/` and place them under `./plugins/`.
It should be quite dead simple - and they'll get auto loaded when put in `./plugins/`.

Features
========

 * Can retrieve and send emails to/from Gmail (IMAP+SMTP)
 * Can retrieve and send sms (via twilio.com)
 * Modular plugin support where the plugins register what events it's interested in.

`matrix_lite.py` in junction with `webrequests.py` are two lite weight libraries to send matrix protocol data over webrequests. Normally you'd do [Python -> Matrix SDK -> Twisted] or something similar, this project ships a light weight library with the following features:

 * register() - Register a username for your bot
 * room_create()
 * join() - Joins a room
 * room_leave()
 * room_invite() - Invites a user to a !room_id:domain.com
 * room_getId(alias)
 * room_getAlias(room_id)
 * room_usermod() - WIP!!
 * send() - Sends a message to a room/person
 * send_encrypted() - Sends encrypted messages to a room/person !!WIP!!
 
Naming standards will change heh, but it's a start :)
