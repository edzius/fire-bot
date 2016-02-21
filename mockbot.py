#!/usr/bin/python

import re
import sys
import xmpp

import table

def debug(msg, *args):
    print("DEBUG %s" % (msg % args))

class Message:

    def __init__(self, user, data, mode=None):
        self.user = user
        self.data = data
        self.mode = mode

    def getFrom(self):
        return self.user

    def getBody(self):
        return self.data

class Client:

    def __init__(self, domain):
        self.hander = None
        self.user = 'guest'
        self.Connection = table.Table()
        self.Connection._sock = 1
        debug("client create: %s", domain)

    def connect(self, server):
        debug("server connect: %s", server)

    def auth(self, node, password):
        debug("auth node: %s (%s)", node, password)

    def RegisterHandler(self, mode, fn):
        self.hander = fn
        debug("register handler: %s", mode)

    def sendInitPresence(self):
        debug("send initial presence")

    def Process(self, count):
        data = sys.stdin.readline()
        match = re.match("^user:\s+(.+)$", data)
        if match:
            self.user = match.group(1)
            debug("switch user: %s", self.user)
            return
        else:
            self.hander(self, Message(self.user, data))

    def send(self, message):
        print(message.getBody())

fakexmpp = table.Table()
fakexmpp.JID = xmpp.JID
fakexmpp.Client = Client
fakexmpp.Message = Message

realxmpp = xmpp
del sys.modules['xmpp']
sys.modules['xmpp'] = fakexmpp

import firebot
