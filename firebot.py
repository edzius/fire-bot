#!/usr/bin/python

import re
import select
import BaseHTTPServer
import xmpp

import table
import settings
import action
import user
import iptv

#####################################################################
# Prerequisites                                                     #
#####################################################################

settings_file = '.settings.conf'
users_file = '.users.json'
handlers_dir = 'actions/'

# Table for global data storing
public = table.Table()
# Load settings
config = settings.load(settings_file)
# Load users list
users = user.UserStore(users_file)
# Load action handlers
actions = action.ActionStore()
actions.load(handlers_dir)

#####################################################################
# XMPP specific methods                                             #
#####################################################################

def handleKnownUser(connection, message, params):
    data = params.data
    user = params.self

    handler, match = actions.select(data, user.access or 0)
    if not handler:
        # TODO(edzius): We may return some friendly message here
        return

    # Set handler match arguments
    params.args = match.groups()
    return handler(connection, message, params)

def handleGuestUser(connection, message, params):
    if not params.self:
        params.users.notice(params.user)
        return 'Your presence is reported to the cheef'
    else:
        # TODO(edzius): We may return some friendly message here
        return

def messageHandler(connection, message):
#    #print(connection)
#    #print(message)
#    #print(dir(connection))
#    #print(dir(message))
#    print('body\t', message.getBody())
#    #print('attrs\t', message.getAttrs())
#    #print('childs\t', message.getChildren())
#    print('data\t', message.getData())
#    print('error\t', message.getError())
#    print('id\t', message.getID())
#    print('name\n', message.getName())
#    print('ns\t', message.getNamespace())
#    print('parent\t',  message.getParent())
#    print('props\t', message.getProperties())
#    print('subject\t', message.getSubject())
#    print('thread\t', message.getThread())
#    print('ts\t', message.getTimestamp())
#    print('type\t', message.getType())
#    #print('payload\t', message.getPayload())
#    print('to\t', str(message.getTo()))
#    print('from\t', str(message.getFrom()))
    data = message.getBody()
    user = message.getFrom()
    if not data or not user:
        return

    params = table.Table()
    params.data = str(data)
    # Set user ID
    params.user = str(user).split('/')[0]
    # Set current user information
    params.self = users.get(params.user)
    params.users = users
    params.actions = actions
    params.public = public

    response = None
    if users.isKnown(params.user):
        response = handleKnownUser(connection, message, params)
    else:
        response = handleGuestUser(connection, message, params)

    if response:
        connection.send(xmpp.Message(message.getFrom(), response , 'chat'))

#####################################################################
# HTTP specific methods                                             #
#####################################################################

class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        query = s.path
        if not re.match("^\/iptv.*$", query):
            s.send_error(404)
            return

        data = dict(re.findall("[\?\&](\w+)=([^&]+)", query))
        if 'hash' not in data:
            s.send_error(400)
            return

        if not public.iptvChangeRequest:
            s.send_error(400)
            return

        checkhash = data['hash']
        if checkhash not in public.iptvChangeRequest:
            s.send_error(400)
            return

        uid = public.iptvChangeRequest[checkhash]
        del public.iptvChangeRequest[checkhash]
        user = users.get(uid)
        if not user:
            s.send_error(400)
            return

        oldIp = user.ip
        newIp = s.client_address[0]

        if not oldIp:
            result = iptv.insertAddress(newIp)
        else:
            result = iptv.changeAddress(newIp, oldIp)

        if not result:
            s.send_error(500)
            return

        user.ip = newIp
        user.save()

        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html>")
        s.wfile.write("<head>")
        s.wfile.write("<title>IP changed!</title>")
        s.wfile.write("</head>")
        s.wfile.write("<body>")
        s.wfile.write("<p><h2>IP changed!</h2></p>")
        s.wfile.write("<p>Old IP: %s</p>" % (oldIp,))
        s.wfile.write("<p>New IP: %s</p>" % (newIp,))
        s.wfile.write("</body>")
        s.wfile.write("</html>")

#####################################################################
# Execution procedures                                              #
#####################################################################

def xmppStep(ctx):
    ctx.chat.Process(1)

def httpStep(ctx):
    ctx.web._handle_request_noblock()

def goOn(ctx, sockets):
    while True:
        (i, o, e) = select.select(sockets.keys(), [], [], 0.1)
        for sock in i:
            sockets[sock](ctx)

xmpp_username = config.get('XMPP', 'USERNAME')
xmpp_password = config.get('XMPP', 'PASSWORD')
xmpp_host = config.get('XMPP', 'SERVER_HOST')
xmpp_port = config.getint('XMPP', 'SERVER_PORT')
http_port = config.getint('HTTP', 'PORT')

jid = xmpp.JID(xmpp_username)
chat = xmpp.Client(jid.getDomain())
chat.connect((xmpp_host, xmpp_port,))
result = chat.auth(jid.getNode(), xmpp_password)

chat.RegisterHandler('message', messageHandler)
chat.sendInitPresence()

web = BaseHTTPServer.HTTPServer(('', http_port), HttpHandler)

ctx = table.Table()
ctx.chat = chat
ctx.web = web

sockets = {
    chat.Connection._sock: xmppStep,
    web.socket._sock: httpStep
}
goOn(ctx, sockets);
