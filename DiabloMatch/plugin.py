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

#from sqlalchemy.orm import mapper, class_mapper
#from sqlalchemy.orm.exc import UnmappedClassError
#from sqlalchemy import func
from sqlalchemy import create_engine, Table, MetaData, func
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import time
#import sqlite3
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
		#self.conn = sqlite3.connect('plugins/DiabloMatch/db.sqlite3')

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
			irc.reply("Sorry, my cache was not initialized. Please repeat your previous command.")
		elif a[0] == 2:
			irc.reply("Still checking. Try again in a few seconds.")
		elif a[0] == 3:
			irc.reply("You're not logged in. Please authenticate with NickServ to use this bot.")
		elif a[0] == 4:
			irc.reply("You were logged in to NickServ as '" + a[1] + "', but your session expired. I've refreshed it; please repeat your previous command.")
		elif a[0] == 5:
			irc.reply("You're logged in to NickServ as '" + a[1] + "'.")
			return a[1]
		else:
			irc.reply("This can't ever happen. Someone must have divided by zero.")
		return False

	def do330(self, irc, msg): #"logged in as" whois response
		nick = ircutils.toLower(msg.args[1])
		account = ircutils.toLower(msg.args[2])
		print nick + " is logged in as " + account
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
				irc.reply("Please specify the battletag you wish to register: !bt register <tag>")
			else:
				if not self._verify_bt(arg2):
					irc.reply("That's not a proper battletag. Use 'BattleTag#1234' format.")
					return
				s = self._check_auth(irc, msg)
				if s:
					#TODO update instead of insert, if exists
					session = Session()
					user = User()
					user.bt = arg2
					user.irc_name = s
					session.add(user)
					session.commit()

					irc.reply("Registered your battletag as " + arg2 + "")
				else:
					irc.reply("Didn't register anything.")
		else:
			try:
				n = arg1.index(":")
			except ValueError:
				n = 0
			if n != 0:
				c = arg1[0:n]
				name = arg1[n+1:]
				session = Session()
				if c == "bt":
					irc.reply("looking up user "+name+" (battletag)")
				elif c == "reddit":
					irc.reply("looking up user "+name+" (Reddit username)")
				elif c == "email":
					irc.reply("looking up user "+name+" (email address)")
				elif c == "irc":
					irc.reply("looking up user "+name+" (IRC services username)")
					users = session.query(User).filter(User.irc_name.like(name.replace("*", "%")))
				elif c == "steam":
					irc.reply("looking up user "+name+" (Steam username)")
				else:
					irc.reply("I don't recognize that field. Known fields: bt, reddit, email, irc, steam")
			else:
				irc.reply("looking up user "+arg1+"")
			for user in users:
				irc.reply(user.pretty_print())
	bt = wrap(bt, [optional('lowered'), optional('lowered')])

	"""
	TODO on any !command, cache the user's whois info
	def doPrivmsg(self, irc, msg):
		if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
			return
		channel = msg.args[0]
		if irc.isChannel(channel):
			if ircmsgs.isAction(msg):
				text = ircmsgs.unAction(msg)
			else:
				text = msg.args[1]
			for url in utils.web.urlRe.findall(text):
				#http://us.battle.net/d3/en/calculator/monk#WVYjRk!YUa!cZZaYb
				m = re.search("battle.net/d3/en/calculator/([\\w-]+)#([\\w\\.]+)!([\\w\\.]+)!([\\w\\.]+)", url)
				if m:
					sk = []
					for f in self._hash_decode(m.group(2)):	#skills
						sk.append(self.skilldata[m.group(1)]["skills"][f])
					out = self.classes_pretty[m.group(1)] + ": "
					for (n, f) in enumerate(self._hash_decode(m.group(4))):	#runes
						if f < 0:
							out += sk[n]["name"] + " (none)"
						else:
							out += sk[n]["name"] + " (" + sk[n]["runes"][f]["name"] + ")"
						out += ", "
					out = out[:-2]
					out += " / "
					for f in self._hash_decode(m.group(3)):	#traits
						out += self.skilldata[m.group(1)]["traits"][f]["name"] + ", "
					out = out[:-2]
					irc.sendMsg(ircmsgs.privmsg(msg.args[0], out))
	"""


Class = DiabloMatch
