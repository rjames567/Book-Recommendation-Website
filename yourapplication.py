#!/usr/bin/python3

#from redmine.lighttpd.net/projects/lighttpd/wiki/Mod_fastcgi
def app(environ, start_response):
	start_response('200 OK', [('Content-Type', 'text/plain')])
	return environ['QUERY_STRING'] + environ['SCRIPT_NAME']
	return ['Hello World!\n']

