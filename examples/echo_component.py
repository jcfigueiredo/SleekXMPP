#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
from optparse import OptionParser

import sleekxmpp
from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp.xmlstream.handler.callback import Callback
from sleekxmpp.xmlstream.matcher.xpath import MatchXPath

from backend import SimpleBackend

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')
else:
    raw_input = input


class EchoComponent(ComponentXMPP):

    """
    A simple SleekXMPP component that echoes messages.
    """

    def __init__(self, jid, secret, server, port):
        ComponentXMPP.__init__(self, jid, secret, server, port)
        self.backend = SimpleBackend()
        # You don't need a session_start handler, but that is
        # where you would broadcast initial presence.

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.

        self.add_event_handler("session_start", self.start)
        # self.add_event_handler("message", self.message)
        self.add_event_handler("changed_subscription",  self.handleXMPPPresenceSubscription)
        self.add_event_handler("got_presence_probe", self.handleXMPPPresenceProbe)
        for event in ["message", "got_online", "got_offline", "changed_status"] :
          self.add_event_handler(event, self.handleIncomingXMPPEvent)
        #
        self.backend.addMessageHandler(self.handleMessageAddedToBackend)

        xpath = "{%s}iq/{cnry:sleep:1}sleep" % self.default_ns

        self.registerHandler(Callback('Sleep command handler', MatchXPath(xpath), self.handle_sleep))

    def start(self, event) :
        self.sendPresence(pfrom='test@localhost', pto='claudio@localhost')
        # self.sendPresence(pfrom='sleep.localhost@localhost', pto='claudio@localhost')
        # for user in self.backend.getAllUsers() :
        #     self.sendPresenceOfAllContactsForUser(user)


    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Since a component may send messages from any number of JIDs,
        it is best to always include a from JID.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        # The reply method will use the messages 'to' JID as the
        # outgoing reply's 'from' JID.
        msg.reply("Thanks for sending\n%(body)s" % msg).send()

    def handleXMPPPresenceSubscription(self, subscription) :
        if subscription["type"] == "subscribe" :
          userJID = subscription["from"]
          self.sendPresenceSubscription(pto=userJID, ptype="subscribed")
          self.sendPresence(pto = userJID)
          self.sendPresenceSubscription(pto=userJID, ptype="subscribe")

    def handleXMPPPresenceProbe(self, event) :
        self.sendPresence(pto = self.backend.getJIDForUser(user))

    def handleIncomingXMPPEvent(self, event) :
        message = event["message"]
        user = self.backend.getUserFromJID(event["jid"])
        self.backend.addMessageFromUser(message, user)

    def handleMessageAddedToBackend(self, message) :
        body = message.user + ": " + message.text
        for subscriberJID in self.backend.getSubscriberJIDs(message.user) :
          self.sendMessage(subscriberJID, body)
        
    def sendPresenceOfAllContactsForUser(self, user) :
        userJID = self.backend.getJIDForUser(user)
        for contact in self.backend.getContacts(user) :
          contactJID = self.getComponentJIDFromUser(contact)
          self.sendPresenceOfContactToUser(contactJID = contactJID, userJID = userJID)

    def sendPresenceOfContactToUser(self, contactJID, userJID) :
        message = self.backend.getLastMessage(contactJID).text
        self.xmpp.sendPresence(pto = userJID, pfrom = contactJID, pshow = message)

    def sendAllContactSubscriptionRequestsToUser(self, userJID) :
        user = self.backend.getUserFromJID(userJID)
        for contact in self.backend.getContacts(user) :
          contactJID = self.getComponentJIDFromUser(contact)
          self.xmpp.sendPresenceSubscription(
              pfrom=contactJID, pto=userJID, ptype="subscribe", pnick=contact)

    def addRecipientToMessage(self, message, recipientJID) :
        contact = self.getUserFromComponentJID(recipientJID)
        return ("@" + contact if contact else "") + " " + message

    def getUserFromComponentJID(self, jid) :
        return jid.split("@",1)[0] if "@" in jid else None

    def getComponentJIDFromUser(self, user) :
        return user + "@" + self.componentDomain
    
    def handle_sleep(self, iq):
        self.sendPresence(pfrom='test@localhost', pto='claudio@localhost', ptype='unavailable')
        print "(iq) = %s" % str(iq)


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-s", "--server", dest="server",
                    help="server to connect to")
    optp.add_option("-P", "--port", dest="port",
                    help="port to connect to")

    opts, args = optp.parse_args()

    if opts.jid is None:
        opts.jid = raw_input("Component JID: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.server is None:
        opts.server = raw_input("Server: ")
    if opts.port is None:
        opts.port = int(raw_input("Port: "))

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Setup the EchoComponent and register plugins. Note that while plugins
    # may have interdependencies, the order in which you register them does
    # not matter.
    xmpp = EchoComponent(opts.jid, opts.password, opts.server, opts.port)
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0004') # Data Forms
    xmpp.registerPlugin('xep_0060') # PubSub
    xmpp.registerPlugin('xep_0199') # XMPP Ping

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")
