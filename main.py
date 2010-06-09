#!/usr/bin/env python
from os import path
from google.appengine.api import memcache, users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.template import render
from google.appengine.ext.webapp.util import run_wsgi_app
from cgi import escape

class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)


class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        greetings = memcache.get('greetings')
        if not greetings:
            greetings = Greeting.all().order('-date').fetch(10)
            memcache.add("greetings", greetings, 10)
        context = {
            'user':      user,
            'greetings': greetings,
            'login':     users.create_login_url(self.request.uri),
            'logout':    users.create_logout_url(self.request.uri),
        }
        tmpl = path.join(path.dirname(__file__), 'static/html/index.html')
        self.response.out.write(render(tmpl, context))
        

class GuestBook(webapp.RequestHandler):
    def post(self):
        greeting = Greeting()
        user = users.get_current_user()
        if user:
            greeting.author = user
        
        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/')
        #self.response.out.write('you wrote: %s ' % escape(self.request.get('content')))


application = webapp.WSGIApplication([('/', MainHandler), 
                                      ('/sign', GuestBook)],
                                     debug=True)

def main():
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
