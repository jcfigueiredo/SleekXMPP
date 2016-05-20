#!/usr/bin/env python
import datetime

def message_compare(m1, m2) :
	return cmp(m1.date, m2.date)

class Message :
	def __init__(self, date, user, text) :
		self.date = date
		self.user = user
		self.text = text

class Backend :
	def __init__(self) :
		self.handlers = []

	def addMessageHandler(self, handler) :
		self.handlers.append(handler)
	
	def notifyMessage(self, message) :
		for handler in self.handlers :
			handler(message)


class SimpleBackend (Backend) :
  def __init__(self) :
    Backend.__init__(self)
    self.messages = {}
    self.contacts = {}

    # Dummy data
    self.messages = {}
    self.contacts = {}
    self.subscribers = {}
    self.jidToUser = {}
    self.userToJID = {}
    self.userPresenceMonitoring = {}
  
  def getMessages(self, user) :
    messages = []
    if self.messages.has_key(user) :
      messages += self.messages[user]

    for contact in self.contacts.get(user, []) :
      if self.messages.has_key(contact) :
        messages += self.messages[contact]
    messages.sort(reverse=True, cmp=message_compare)
    return messages

  def getLastMessage(self, user) :
    messages = self.getMessages(user)
    if len(messages) > 0 :
      return messages[0]
    else :
      return Message(None, user, '')

  def addMessageFromUser(self, text, user) :
    if len(text) > 0 and self.getLastMessage(user) != text :
      message = Message(datetime.datetime.today(), user, text)
      self.messages.setdefault(user,[]).append(message)
      self.notifyMessage(message)

  def getAllUsers(self) :
    return self.messages.keys()
  
  def getContacts(self, user) :
    return self.contacts.get(user, [])
  
  def getJIDForUser(self, user) :
    return self.userToJID[user]

  def getUserHasJID(self, user) :
    return self.userToJID.has_key(user)

  def getShouldMonitorPresenceFromUser(self, user):
    return self.userPresenceMonitoring[user]

  def setShouldMonitorPresenceFromUser(self, user, state):
    self.userPresenceMonitoring[user] = state

  def getSubscriberJIDs(self, user) :
    subscribers = []
    #for subscriber in self.subscribers.get(user, []) + [user] :
    for subscriber in self.subscribers.get(user, []) :
      if self.userToJID.has_key(subscriber) :
        subscribers.append(self.userToJID[subscriber])
    return subscribers
  
  def getUserFromJID(self, user) :
    return self.jidToUser.get(user.split('/',1)[0], None)

  def addContact(self, user, contact) :
    if not self.contacts.has_key(user) :
      self.contacts[user] = []
    self.contacts.setdefault(user, []).append(contact)

  def registerXMPPUser(self, user, password, fulljid) :
    barejid = fulljid.split('/', 1)[0]
    self.jidToUser[barejid] = user
    self.userToJID[user] = barejid
    return True

