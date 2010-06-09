#!/usr/bin/env python
from os import path
from google.appengine.api import mail, memcache, users, xmpp
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.template import render
from google.appengine.ext.webapp.util import run_wsgi_app

class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)

def getGreetings(fetch=10):
    greetings = memcache.get('greetings')
    if not greetings:
        greetings = Greeting.all().order('-date').fetch(fetch)
        memcache.add("greetings", greetings, 10)
    return greetings

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        greetings = getGreetings()
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
            name = user.nickname()
        else:
            name = 'anonymous'
        greeting.content = self.request.get('content')
        greeting.put()
        memcache.delete('greetings')
        mail.send_mail(
            user and user.email() or 'postmaster@doinggd.appspotmail.com', # from
            'linchuan.cheng@gmail.com', # to
            'GuestBook post from %s' % name, # subj
            '%s wrote:\r\n\r\n"%s"' % (name, greeting.content), # body
        )
        self.redirect('/')

class GBChatBot(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        cmd = message.body[0:5].lower()
        if cmd == '/list':
            greetings = getGreetings(5)
            reply = '%s\r\n\r\n%s' % (
                '5 Most Recent Guestbook entries:',
                '\r\n'.join(['%s: %s' % (
                    '*%s*' % g.author.nickname() if g.author else '_anonymous_',
                    g.content[:40]) for g in greetings
                
            ]))
        elif cmd == '/help':
            reply = '''
Guestbook Chatbot 0.2
Supported commands are:
     */list* (5 most recent entries)
     */help* (this help msg)'''
        else:
            reply = '''
Command "%s" not supported!
Send "/help" for command list.''' % message.body
            message.reply(reply)

application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/sign', GuestBook),
    ('/_ah/xmpp/message/chat/', GBChatBot),
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

