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

class User(object):
	def __init__(self):
		pass

	def __repr__(self):
		return "<User('%s')>" % (self.irc_name)

	def pretty_print(self):
		out = ""
		for k, v in self.__dict__.iteritems():
			if k not in ["id", "_sa_instance_state"] and v != u"" and v != 0:
				out += str(k) + ": " + str(v) + ", "
		return out[:-2]

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

	def _verify_bt(self, tag):
		return re.match(r"\w{1,32}#\d{4,8}$", tag) != None

	def _check_auth(self, irc, msg):
		a = self._get_services_account(irc, ircutils.toLower(msg.nick))
		if a[0] == 1:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Sorry, my cache was not initialized. Please repeat your previous command."))
		elif a[0] == 2:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "Still checking. Try again in a few seconds."))
		elif a[0] == 3:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You're not logged in. Please authenticate with NickServ to use this bot."))
		elif a[0] == 4:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You were logged in to NickServ as '" + a[1] + "', but your session expired. I've refreshed it; please repeat your previous command."))
		elif a[0] == 5:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "You're logged in to NickServ as '" + a[1] + "'."))
			return a[1]
		else:
			irc.sendMsg(ircmsgs.privmsg(msg.nick, "This can't ever happen. Someone must have divided by zero."))
		return False

	def do330(self, irc, msg): #"logged in as" whois response
		nick = ircutils.toLower(msg.args[1])
		account = ircutils.toLower(msg.args[2])
		self._whois[nick] = (account, time.time())
		return
		nick = ircutils.toLower(msg.args[1])
		if (irc, nick) not in self._whois:
			return
		else:
			self._whois[(irc, nick)][-1][msg.command] = msg

	def do318(self, irc, msg):	#end of whois responses
		#if we get this and didn't get a 330, then the user is not logged in
		nick = ircutils.toLower(msg.args[1])
		if self._whois[nick] == None:
			self._whois[nick] = -1		#-1 means whois complete and not logged in

	def bt(self, irc, msg, args, arg1, arg2):
		"""Add the help for "@plugin help DiabloMatch" here
		This should describe *how* to use this plugin."""
		if arg1 == "register":
			if arg2 == None:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Please specify the battletag you wish to register: !bt register BattleTag#1234"))
			else:
				if not self._verify_bt(arg2):
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "That's not a proper battletag. Use 'BattleTag#1234' format."))
					return
				s = self._check_auth(irc, msg)
				if s:
					session = Session()
					try:
						user = session.query(User).filter(User.irc_name == s).one()
					except NoResultFound:	#we want irc_name to be unique, even though it's not a primary key
						user = User()
					user.bt = arg2
					user.irc_name = s
					session.add(user)
					session.commit()

					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Registered your battletag as " + arg2 + ""))
				else:
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "Didn't register anything."))
		elif arg1 == None:
			s = self._check_auth(irc, msg)
			if s:
				session = Session()
				user = session.query(User).filter(User.irc_name == s).one()	#only one because irc_name is unique
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "Your battletag is " + user.pretty_print()))
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
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+name+" (battletag)"))
				elif c == "reddit":
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+name+" (Reddit username)"))
				elif c == "email":
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+name+" (email address)"))
				elif c == "irc":
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+name+" (IRC services username)"))
					users = session.query(User).filter(User.irc_name.like(name.replace("*", "%")))
				elif c == "steam":
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+name+" (Steam username)"))
				else:
					irc.sendMsg(ircmsgs.privmsg(msg.nick, "I don't recognize that field. Known fields: bt, reddit, email, irc, steam"))
			else:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, "looking up user "+arg1+""))
				users = session.query(User).filter(or_(
						User.bt.like(arg1.replace("*", "%")),
						User.reddit_name.like(arg1.replace("*", "%")),
						User.email.like(arg1.replace("*", "%")),
						User.irc_name.like(arg1.replace("*", "%")),
						User.steam_name.like(arg1.replace("*", "%"))))
			for user in users:
				irc.sendMsg(ircmsgs.privmsg(msg.nick, user.pretty_print()))
	bt = wrap(bt, [optional('lowered'), optional('lowered')])

	#on any channel activity, cache the user's whois info
	def doPrivmsg(self, irc, msg):
		if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
			return
		if irc.isChannel(msg.args[0]):
			self._get_services_account(irc, ircutils.toLower(msg.nick))

Class = DiabloMatch
