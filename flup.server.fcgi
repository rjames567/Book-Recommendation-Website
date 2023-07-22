#!/usr/bin/env python3.10
from flup.server.fcgi import WSGIServer
#from yourapplication import app
from wsgi import Application as app

#from redmine.lighttpd.net/projects/lighttpd/wiki/Mod_fastcgi
def app2(environ, start_response):
	start_response('200 OK', [('Content-Type', 'text/plain')])
	return ['Hello Worldly World!\n']

if __name__ == '__main__':
    WSGIServer(app).run()

