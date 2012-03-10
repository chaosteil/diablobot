###
# Copyright (c) 2012, listen2, Chaosteil
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks

from sqlalchemy import create_engine, Table, MetaData, func, or_
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import time
import re
import pytz
from datetime import datetime

class User(object):
	quickfields = [("irc_name", "IRC"), ("reddit_name", "Reddit"), ("steam_name", "Steam"), ("bt", "Battletag")]

	def __init__(self):
		pass

	def __repr__(self):
		return "<User('%s')>" % (self.irc_name)

	def pretty_print(self, r=True):
		out = ""
		for f in User.quickfields:
			v = getattr(self, f[0])
			if v != None and v != 0:
				out += "" + f[1] + ": " + v + ", "
		out = out[:-2]
		if r and self.realm != None:
			out += ", Realm: " + self.realm
		return out

	def full_print(self):
		out = []
		out.append(self.pretty_print(r=False))
		if self.realm != None:
			out.append("Realm: " + self.realm)
		if self.cmt != None:
			out.append("Comment: " + self.cmt)
		if self.tz != None:
			tz_to = pytz.timezone(self.tz)
			tz_from = pytz.timezone("America/New_York")
			tm = datetime.now().replace(tzinfo=tz_from)
			tm_to = tm.astimezone(tz_to)
			out.append("Local time: " + tm_to.strftime("%d %b %H:%M:%S (%Z %z)"))
		if self.url != None:
			out.append("URL: " + self.url)
		return out

#engine = create_engine('sqlite:///plugins/DiabloMatch/db.sqlite3', echo=True)
engine = create_engine('sqlite:///plugins/DiabloMatch/db.sqlite3')
Session = sessionmaker(bind=engine)
meta = MetaData()
meta.bind = engine
user_table = Table('users', meta, autoload=True)
mapper(User, user_table)


class DiabloMatch(callbacks.Plugin):
	"""Add the help for "@plugin help DiabloMatch" here
	This should describe *how* to use this plugin."""
	_whois = {}
	bt_regexp = re.compile(r"\w{1,32}#\d{4,8}$")

	def __init__(self, irc):
		super(DiabloMatch, self).__init__(irc)

	def _get_services_account(self, irc, nick):
		if nick not in self._whois.keys():
			irc.queueMsg(ircmsgs.whois(nick, nick))
			self._whois[nick] = None	#None means whois in process
			return (1, )
		elif self._whois[nick] == None:
			return (2, )
		elif self._whois[nick] == -1:
			return (3, )
		else:	#user was authed in the past
			if time.time() - self._whois[nick][1] > 36000:	#ten hours
				irc.queueMsg(ircmsgs.whois(nick, nick))
				return (4, self._whois[nick][0])
			else:
				return (5, self._whois[nick][0])

	def _check_auth(self, irc, msg):
		a = self._get_services_account(irc, msg.nick)
		if a[0] == 1:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Sorry, my cache was not initialized. Please repeat your previous command."))
		elif a[0] == 2:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Still checking. Try again in a few seconds."))
		elif a[0] == 3:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You're not logged in. Please authenticate with NickServ so I know who you are."))
		elif a[0] == 4:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You were logged in to NickServ as '" + a[1] + "', but your session expired. I've refreshed it; please repeat your previous command."))
		elif a[0] == 5:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You're logged in to NickServ as '" + a[1] + "'."))
			return a[1]
		else:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "This can't ever happen. Someone must have divided by zero."))
		return False

	def do330(self, irc, msg): #"logged in as" whois response
		nick = msg.args[1]
		account = msg.args[2]
		self._whois[nick] = (account, time.time())

	def do318(self, irc, msg):	#end of whois responses
		#if we get this and didn't get a 330, then the user is not logged in
		nick = msg.args[1]
		if self._whois[nick] == None:
			self._whois[nick] = -1		#-1 means whois complete and not logged in

	def bt(self, irc, msg, args, arg1, arg2):
		"""[\37user]  |  register \37Battletag#1234
		Shows user information. \37user may be prefixed with irc:, steam:, reddit:, email:, or bt:, and may contain the wildcard *. If \37user is not supplied, your own information will be displayed.
		If the first argument is register, the given \37battletag will be registered as yours.
		"""
		if arg1 == "register":
			if arg2 == None:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Please specify the battletag you wish to register: !bt register BattleTag#1234"))
			else:
				self.btset(irc, msg, ["bt", arg2])
		elif arg1 == None:
			s = self._check_auth(irc, msg)
			if s:
				session = Session()
				try:
					user = session.query(User).filter(func.lower(User.irc_name) == func.lower(s)).one()	#only one because irc_name is unique
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Your battletag is " + user.pretty_print()))
				except NoResultFound:
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "No battletag found"))
		else:
			try:
				n = arg1.index(":")
			except ValueError:
				n = 0
			session = Session()
			if n != 0:
				c = arg1[0:n]
				name = arg1[n+1:]
				if c == "bt":
					users = session.query(User).filter(func.lower(User.bt).like(func.lower(name.replace("*", "%"))))
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (battletag). " + str(users.count()) + " results."))
				elif c == "reddit":
					users = session.query(User).filter(func.lower(User.reddit_name).like(func.lower(name.replace("*", "%"))))
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (Reddit username). " + str(users.count()) + " results."))
				elif c == "email":
					users = session.query(User).filter(func.lower(User.email).like(func.lower(name.replace("*", "%"))))
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (email address). " + str(users.count()) + " results."))
				elif c == "irc":
					users = session.query(User).filter(func.lower(User.irc_name).like(func.lower(name.replace("*", "%"))))
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (IRC services username). " + str(users.count()) + " results."))
				elif c == "steam":
					users = session.query(User).filter(func.lower(User.steam_name).like(func.lower(name.replace("*", "%"))))
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (Steam username). " + str(users.count()) + " results."))
				else:
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "I don't recognize that field. Known fields: bt, reddit, email, irc, steam"))
			else:
				users = session.query(User).filter(or_(
						func.lower(User.bt).like(func.lower(arg1.replace("*", "%"))),
						func.lower(User.reddit_name).like(func.lower(arg1.replace("*", "%"))),
						func.lower(User.email).like(func.lower(arg1.replace("*", "%"))),
						func.lower(User.irc_name).like(func.lower(arg1.replace("*", "%"))),
						func.lower(User.steam_name).like(func.lower(arg1.replace("*", "%")))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+arg1+". " + str(users.count()) + " results."))
			for user in users:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, user.pretty_print()))
	bt = wrap(bt, [optional('anything'), optional('anything')])

	def btinfo(self, irc, msg, args, arg1):
		"""[\37user]
		Shows detailed user information. \37user may be prefixed with irc:, steam:, reddit:, email:, or bt:, and may contain the wildcard *. If \37user is not supplied, your own information will be displayed.
		"""
		if arg1 == None:
			arg1 = "irc:" + self._check_auth(irc, msg)
		try:
			n = arg1.index(":")
		except ValueError:
			n = 0
		session = Session()
		if n != 0:
			c = arg1[0:n]
			name = arg1[n+1:]
			if c == "bt":
				users = session.query(User).filter(func.lower(User.bt).like(func.lower(name.replace("*", "%"))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (battletag). " + str(users.count()) + " results."))
			elif c == "reddit":
				users = session.query(User).filter(func.lower(User.reddit_name).like(func.lower(name.replace("*", "%"))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (Reddit username). " + str(users.count()) + " results."))
			elif c == "email":
				users = session.query(User).filter(func.lower(User.email).like(func.lower(name.replace("*", "%"))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (email address). " + str(users.count()) + " results."))
			elif c == "irc":
				users = session.query(User).filter(func.lower(User.irc_name).like(func.lower(name.replace("*", "%"))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (IRC services username). " + str(users.count()) + " results."))
			elif c == "steam":
				users = session.query(User).filter(func.lower(User.steam_name).like(func.lower(name.replace("*", "%"))))
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+name+" (Steam username). " + str(users.count()) + " results."))
			else:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "I don't recognize that field. Known fields: bt, reddit, email, irc, steam"))
		else:
			users = session.query(User).filter(or_(
					func.lower(User.bt).like(func.lower(arg1.replace("*", "%"))),
					func.lower(User.reddit_name).like(func.lower(arg1.replace("*", "%"))),
					func.lower(User.email).like(func.lower(arg1.replace("*", "%"))),
					func.lower(User.irc_name).like(func.lower(arg1.replace("*", "%"))),
					func.lower(User.steam_name).like(func.lower(arg1.replace("*", "%")))))
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Looking up user "+arg1+". " + str(users.count()) + " results."))
		for user in users:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "User details. Fields marked with a * are unvalidated."))
			for line in user.full_print():
				irc.sendMsg(ircmsgs.privmsg(msg.nick, line))
	btinfo = wrap(btinfo, [optional('anything')])

	def btset(self, irc, msg, args, arg1, arg2):
		"""\37field \37value
		Modifies your user info. Invoke btset list to see a list of available fields
		"""
		if arg1.lower() == "list":	#or arg1.lower() not in []:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Here's a list of available fields: (not yet implemented)."))
			return
		if arg2 == None:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Here's the current value of " + arg1 + ": (not yet implemented)."))
			return
		ircname = self._check_auth(irc, msg)
		if not ircname:
			return
		if arg1 == "bt":
			if DiabloMatch.bt_regexp.match(arg2) == None:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "That's not a proper battletag. Use 'BattleTag#1234' format."))
				return
			session = Session()
			try:
				user = session.query(User).filter(func.lower(User.irc_name) == func.lower(ircname)).one()
			except NoResultFound:	#we want irc_name to be unique, even though it's not a primary key
				user = User()
				user.irc_name = ircname
			user.bt = arg2
			session.add(user)
			session.commit()

			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Registered your battletag as " + arg2 + ""))
		elif arg1 == "tz":
			try:
				pytz.timezone(arg2)
			except pytz.UnknownTimeZoneError as e:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Unknown time zone " + str(e)))
				return
			session = Session()
			try:
				user = session.query(User).filter(func.lower(User.irc_name) == func.lower(ircname)).one()
			except NoResultFound:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Register first."))
				return
			user.tz = arg2
			session.add(user)
			session.commit()
	btset = wrap(btset, ['anything', optional('text')])

	#on any channel activity, cache the user's whois info
	def doPrivmsg(self, irc, msg):
		if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
			return
		if irc.isChannel(msg.args[0]):
			self._get_services_account(irc, msg.nick)

Class = DiabloMatch
