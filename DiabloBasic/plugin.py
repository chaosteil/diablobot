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

import re
import json
import random
import time, pytz
from datetime import datetime
from dateutil.parser import parse

class DiabloBasic(callbacks.Plugin):
	"""Add the help for "@plugin help DiabloBasic" here
	This should describe *how* to use this plugin."""
	hash_base = "aZbYcXdWeVfUgThSiRjQkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA0123456789+/"
	classes = ["barbarian", "demon-hunter", "monk", "witch-doctor", "wizard", "follower"]
	classes_pretty = {"barbarian":"Barbarian", "demon-hunter":"Demon Hunter", "monk":"Monk", "witch-doctor":"Witch Doctor", "wizard":"Wizard", "follower":"Follower"}
	skilldata = {}

	def __init__(self, irc):
		super(DiabloBasic, self).__init__(irc)
		for c in self.classes:
			f = open("plugins/DiabloBasic/data/"+c+".json", "r")
			self.skilldata[c] = json.load(f)
			f.close()
		f = open("plugins/DiabloBasic/data/quotes.json", "r")
		self.quotes = json.load(f)
		f.close()

	def _quotehelp(self):
		out = "Available quote sources: "
		for f in self.quotes.keys():
			out += f + ", "
		return out[:-2]

	def quote(self, irc, msg, args, charname):
		"""Returns a random quote from the character specified, or from anyone if no character specified.
		"""
		if not charname:
			q = self.quotes[random.choice(self.quotes.keys())]
			irc.sendMsg(ircmsgs.privmsg(msg.args[0], q["name"] + ": " + random.choice(q["quotes"])))
		elif charname == "list":
			irc.reply(self._quotehelp())
		else:
			try:
				irc.sendMsg(ircmsgs.privmsg(msg.args[0], self.quotes[charname]["name"] + ": " + random.choice(self.quotes[charname]["quotes"])))
			except KeyError:
				irc.reply("I don't have any quotes from " + charname + ". " + self._quotehelp())
	quote = wrap(quote, [optional('lowered')])

	def skill(self, irc, msg, args, charname):
		"""takes zero or one arguments

		Returns a random quote from the character specified, or from anyone if no character specified.
		"""
		if not charname:
			irc.reply("here's a quote from a random character")
		else:
			irc.reply("here's a quote from "+charname)
	skill = wrap(skill, [optional('lowered')])

	def item(self, irc, msg, args, charname):
		"""takes zero or one arguments

		Returns a random quote from the character specified, or from anyone if no character specified.
		"""
		if not charname:
			irc.reply("here's a quote from a random character")
		else:
			irc.reply("here's a quote from "+charname)
	item = wrap(item, [optional('lowered')])

	def _hash_decode(self, h):
		a = []
		for f in h:
			a.append(self.hash_base.find(f));
		return a

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

	def tz(self, irc, msg, args, arg1, arg2, arg3):
		"""!tz [<source timezone>] <your timezone> <time to convert>

		Converts the given time from source timezone to your timezone. You may specify 'now' as the time to convert. If no source timezone is specified, Pacific US (Blizzard) time is used.
		"""
		try:
			if not arg3:
				tz_from = pytz.timezone("US/Pacific")
				tz_to = pytz.timezone(arg1)
				tm = arg2
			else:
				tz_from = pytz.timezone(arg1)
				tz_to = pytz.timezone(arg2)
				tm = arg3
		except pytz.UnknownTimeZoneError as e:
			irc.reply("Unknown time zone " + str(e))
			return
		if tm == "now":
			tm = time.time()
		else:
			tm = parse(tm)
		"""
		print tz_from.__dict__
		{'_dst': datetime.timedelta(0),
		'_utcoffset': datetime.timedelta(-1, 57600),
		'_tzinfos': {
			(datetime.timedelta(-1, 57600), datetime.timedelta(0), 'PST'): <DstTzInfo 'US/Pacific' PST-1 day, 16:00:00 STD>,
			(datetime.timedelta(-1, 61200), datetime.timedelta(0, 3600), 'PPT'): <DstTzInfo 'US/Pacific' PPT-1 day, 17:00:00 DST>,
			(datetime.timedelta(-1, 61200), datetime.timedelta(0, 3600), 'PWT'): <DstTzInfo 'US/Pacific' PWT-1 day, 17:00:00 DST>,
			(datetime.timedelta(-1, 61200), datetime.timedelta(0, 3600), 'PDT'): <DstTzInfo 'US/Pacific' PDT-1 day, 17:00:00 DST>},
			'_tzname': 'PST'
		}
		"""
		print tm
		print tm.timetuple()
		print time.mktime(tm.timetuple())
		print "\n"
		print tm.timetuple()
		print str(int(tz_from["utcoffset"]))
		return
		tm_from = tz_from.localize(datetime.fromtimestamp(tm))
		irc.reply(str(tm_from) + " tm_from")
		tm_to = tz_to.localize(tz_from)
		irc.reply(str(tm_to) + " tm_to")
		#utc_dt = pytz.utc.localize(datetime.utcfromtimestamp(tm))
		#irc.reply(str(utc_dt) + " utc")
		#tm_to = tz_to.normalize(utc_dt.astimezone(tz_to))
		#irc.reply(str(tm_to) + " tm_to")
		#utc_dt2 = utc.normalize(tm_to.astimezone(pytz.utc))
		#irc.reply(utc_dt2)
		irc.reply(str(tz_to) + ": " + str(tm_to))
	tz = wrap(tz, ['anything', 'anything', optional('anything')])

Class = DiabloBasic
