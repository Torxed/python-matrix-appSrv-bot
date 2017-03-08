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
