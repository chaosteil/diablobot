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
import pytz
from datetime import datetime
from dateutil.parser import parse
import urllib2

class DiabloBasic(callbacks.Plugin):
	"""Add the help for "@plugin help DiabloBasic" here
	This should describe *how* to use this plugin."""
	#threaded = True
	hash_base = "aZbYcXdWeVfUgThSiRjQkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA0123456789+/"
	classes = ["barbarian", "demon-hunter", "monk", "witch-doctor", "wizard", "follower"]
	classes_pretty = {"barbarian":"Barbarian", "demon-hunter":"Demon Hunter", "monk":"Monk", "witch-doctor":"Witch Doctor", "wizard":"Wizard", "follower":"Follower"}
	skilldata = {}
	#_regular_streams = ["rdiablo", "DrZealotTV"]
	#_dstream_re = re.compile("diablo", re.IGNORECASE)
	_dstream_re = re.compile("starcraft", re.IGNORECASE)

	def __init__(self, irc):
		super(DiabloBasic, self).__init__(irc)
		for c in self.classes:
			f = open("plugins/DiabloBasic/data/"+c+".json", "r")
			self.skilldata[c] = json.load(f)
			f.close()
		f = open("plugins/DiabloBasic/data/quotes.json", "r")
		self.quotes = json.load(f)
		f.close()
		DiabloBasic._qcount = 0
		for c in self.quotes.values():
			DiabloBasic._qcount += len(c["quotes"])

	def _quotehelp(self):
		out = "Available quote sources: "
		for f in sorted(self.quotes.keys()):
			out += f + ", "
		out = out[:-2]
		out += " (" + str(DiabloBasic._qcount) + " quotes)"
		return out

	def quote(self, irc, msg, args, charname):
		"""[\37character]
		Returns a random quote from \37character, or from a random character if none is specified.
		"""
		if not charname:
			if random.randrange(0, 999) == 0:	#this won't show up in the list of quote sources. it's a secret!
				irc.sendMsg(ircmsgs.privmsg(msg.args[0], "Cow: Mooooooo!"))
				return
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
		"""[\37source_timezone] \37your_timezone \37time_to_convert  |  \37your_timezone now

		Converts the given time from \37source_timezone to \37your_timezone. If no source timezone is specified, Pacific US (Blizzard) time is used. If 'now' is used as the time to covert, the source timezone is assumed to be US/Pacific (Blizzard).
		"""
		try:
			if not arg3:
				tz_to = pytz.timezone(arg1)
				if arg2 == "now":
					tz_from = pytz.timezone("America/New_York")
					tm = datetime.now().replace(tzinfo=tz_from)
				else:
					tz_from = pytz.timezone("America/Los_Angeles")
					tm = parse(arg2).replace(tzinfo=tz_from)
			else:
				try:
					tz_from = pytz.timezone(arg1)
					tz_to = pytz.timezone(arg2)
					tm = parse(arg3).replace(tzinfo=tz_from)
				except ValueError:
					return
		except pytz.UnknownTimeZoneError as e:
			if str(e) == "'Blizzard'":
				irc.reply("Blizzard time: Soon")
			else:
				irc.reply("Unknown time zone " + str(e))
			return
		tm_to = tm.astimezone(tz_to)
		irc.reply(tm_to.strftime("%d %b %H:%M:%S (%Z %z)"))
	tz = wrap(tz, ['anything', 'anything', optional('anything')])

	def rules(self, irc, msg, args):
		"""
		Shows the rules for #diablo and #bazaar.
		"""
		rs = [
			"All topics are allowed, but Diablo should always take precedence.",
			"Be polite and respectful of others.",
			"Do not disrupt conversation with spam or bot activities.",
			"Use #bazaar for item trading discussion.",
			"Do not sell, offer to sell, or seek sale of beta keys.",
			"Follow instructions given by the channel operators.",
			"Abide by the EsperNet Charter and Acceptable Use Policy (http://esper.net/charter.php)",
			"See http://bit.ly/wEkLDN for more details."
		]
		irc.sendMsg(ircmsgs.privmsg(msg.nick, "Channel rules for #diablo and #bazaar"))
		for n, v in enumerate(rs):
			irc.sendMsg(ircmsgs.privmsg(msg.nick, str(n+1) + ". " + v))
		irc.sendMsg(ircmsgs.privmsg(msg.nick, "End of rules"))
	#rules = wrap(rules)

	def streams(self, irc, msg, args, sname):
		"""[<\37stream> ...]

		Displays whether \37stream is currently live. If no stream is specified, it lists the status of all the regular streams.
		"""
		data = urllib2.urlopen("http://api.justin.tv/api/stream/list.json")
		j = json.load(data)

		irc.reply("Active Diablo streams on twitch.tv or justin.tv:")
		i = 0
		for c in j:
			if i >= 6:
				irc.reply("And more!")
				return
			try:
				if DiabloBasic._dstream_re.match(c["meta_game"]):
					irc.reply(c["channel"]["channel_url"] + " (" + c["meta_game"] + ")")
					i += 1
			except:
				pass

	streams = wrap(streams, [optional('anything')])

Class = DiabloBasic
