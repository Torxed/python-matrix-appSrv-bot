c = {}
c['homeserver'] = '127.0.0.1'
c['hs_port'] = 8008
c['domain'] = 'matrix.org'
c['callbacks'] = '127.0.0.1'
c['callback_port'] = 9999

c['user'] = 'twilio' # This just happned to be what I started out with in tools/app_gen.py
c['main_room'] = '!lEtjrGgsVHfpTHhxtT' # The main room to hang around in, if None we won't join.

c['api'] = {}
c['api']['base_url'] = '/_matrix/'
c['api']['access_token'] = '<whatever tools/app_gen.py> generates'
c['api']['apppli_token'] = '<whatever tools/app_gen.py> generates'

c['twilio'] = {}
c['twilio']['as'] = "..."   #Account Sid
c['twilio']['at'] = "..."   #Auth Token
c['twilio']['from'] = "+460000000000"

c['gmail'] = {}
c['gmail']['username'] = 'user@gmail.com'
c['gmail']['password'] = 'appicationPassword / account password'
c['gmail']['mail_room'] = '!AShvPqdHtSXhfoaSzf' # I'm working on grouping mails unless you respond to them.

c['misc'] = {}
c['misc']['allowed_users'] = {'@anton:matrix.org'} # Who's allowed to do "sms: ..." or "mail: ..."

c['plugins'] = {}
c['event_hooks'] = {}

## == Kids, if you've ever learned consistency thinking..
##    This is a prime example of what you should'nt do.
##    But if you've tought to be lazy, this is what you'll do anyway.
##
##    making the config truly global even in submodules:
__builtins__['c'] = c