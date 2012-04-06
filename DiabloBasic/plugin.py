# -*- coding: utf-8 -*-
###
# listen2, Chaosteil 2012
#
# This work has been released into the public domain by the authors. This
# applies worldwide.
#
# If this is not legally possible, the authors grant any entity the right to
# use this work for any purpose, without any conditions, except those conditions
# required by law.
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
import pytz, time
from datetime import datetime
from dateutil.parser import parse
import httplib2

import sys
if "/home/listen2/dbot/plugins/DiabloCommon" not in sys.path:
     sys.path.append("/home/listen2/dbot/plugins/DiabloCommon")
import DiabloCommon

class DiabloBasic(callbacks.Plugin):
    """Add the help for "@plugin help DiabloBasic" here
    This should describe *how* to use this plugin."""
    #threaded = True

    # Skill Info
    hash_base = "aZbYcXdWeVfUgThSiRjQkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA0123456789+/"
    classes = {
        "barbarian": "Barbarian",
        "demon-hunter": "Demon Hunter",
        "monk": "Monk",
        "witch-doctor": "Witch Doctor",
        "wizard": "Wizard",
        "follower": "Follower"
    }
    skilldata = {}

    # Stream info. note lowercase.
    _dstream_regulars = [
        "rdiablo",
        "drzealottv",
        "theblinks"
    ]
    _dstream_regulars_json = {}
    _dstream_re = re.compile("diablo", re.IGNORECASE)

    def __init__(self, irc):
        super(DiabloBasic, self).__init__(irc)

        # Load class data
        for c in self.classes.keys():
            with open("/home/listen2/dbot/plugins/DiabloBasic/data/"+c+".json", "r") as f:
                self.skilldata[c] = json.load(f)

        # Load quotes
        with open("/home/listen2/dbot/plugins/DiabloBasic/data/quotes.json", "r") as f:
            self.quotes = json.load(f)
        self.quote_count = 0
        for c in self.quotes.values():
            self.quote_count += len(c["quotes"])

        # Init stream checking
        DiabloBasic._dstream_time = 0

    def printQuote(self, irc, name, message):
        irc.reply("%s: %s" % (name, message), prefixNick=False)

    def quote(self, irc, msg, args, charname):
        """[\37character]
        Returns a random quote from \37character, or from a random character if none is specified.
        """
        # Lists all available quote sources
        if charname == "list":
            irc.reply('Available quote sources: %s (%d quotes)' % \
                (', '.join(sorted(self.quotes.keys())), self.quote_count))

        # Picks a random quote
        elif not charname:
            # this won't show up in the list of quote sources. it's a secret!
            if random.randint(0, 999) == 0:
                self.printQuote(irc, "Cow", "Mooooooo! Moo moo moo moo moo!")
            else:
                q = self.quotes[random.choice(self.quotes.keys())]
                self.printQuote(irc, q["name"], random.choice(q["quotes"]))

        # Help text
        elif charname not in self.quotes:
            irc.reply("I don't have any quotes from %s. Available quote sources: %s (%d quotes)" % \
                (charname, ", ".join(sorted(self.quotes.keys())), self.quote_count))

        # Prints a quote of the character
        else:
            q = self.quotes[charname]
            self.printQuote(irc, q["name"], random.choice(q["quotes"]))

    quote = wrap(quote, [optional('lowered')])

    def _hash_decode(self, h):
        return [self.hash_base.find(f) for f in h]

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
                    sk = [self.skilldata[m.group(1)]["skills"][f] for f in self._hash_decode(m.group(2))]
                    out = self.classes[m.group(1)] + ": " #classname
                    out += ", ".join(["%s (%s)" % (sk[n]["name"], ("none" if f < 0 else sk[n]["runes"][f]["name"])) for (n, f) in enumerate(self._hash_decode(m.group(4)))]) #skills
                    out += " / "
                    out += ", ".join([self.skilldata[m.group(1)]["traits"][f]["name"] for f in self._hash_decode(m.group(3))]) #traits
                    irc.reply(out, prefixNick=False)
                    return  #no need no check the other url formats.
                #https://twitter.com/#!/Nyzaris/status/179599382814011392
                m = re.search("twitter.com/#!/.+/status/(\d+)", url)
                if m:
                    h = httplib2.Http(".cache")
                    resp, j = h.request("http://api.twitter.com/1/statuses/show/%s.json" % m.group(1), "GET")
                    tjson = json.loads(j)
                    irc.reply("%s (%s): %s" % (tjson["user"]["screen_name"], tjson["user"]["name"], tjson["text"]), prefixNick=False)
                    return
                if url.find("reddit.com/r/") != -1:
                    h = httplib2.Http(".cache")
                    resp, j = h.request(url + ".json?limit=1", "GET")
                    f = json.loads(j)[0]["data"]["children"][0]["data"]

                    if f["is_self"]:
                        irc.reply("Reddit: [%d] %s (%s) by %s %s ago. %d comment%s." % (f["score"], f["title"], f["domain"], f["author"], DiabloCommon.timeago(time.time() - f["created_utc"]), f["num_comments"], "s" if f["num_comments"] != 1 else ""), prefixNick=False)
                    else:
                        irc.reply("Reddit: [%d] %s (%s) by %s %s ago. %d comment%s." % (f["score"], f["title"], f["url"], f["author"], DiabloCommon.timeago(time.time() - f["created_utc"]), f["num_comments"], "s" if f["num_comments"] != 1 else ""), prefixNick=False)
                    return

    def tz(self, irc, msg, args, arg1, arg2, arg3):
        """[\37source_timezone] \37your_timezone \37time_to_convert  |  \37your_timezone now

        Converts the given time from \37source_timezone to \37your_timezone. If no source timezone is specified, Pacific US (Blizzard) time is used. If 'now' is used as the time to covert, the source timezone is assumed to be US/Pacific (Blizzard).
        """
        try:
            if not arg3:
                tz_to = pytz.timezone(arg1)
                if arg2 == "now":
                    tz_from = pytz.timezone("America/New_York")
                    tm = datetime.now(pytz.utc)
                else:
                    try:
                        tz_from = pytz.timezone("America/Los_Angeles")
                        tm = tz_from.localize(parse(arg2))
                    except ValueError:
                        return
            else:
                try:
                    tz_from = pytz.timezone(arg1)
                    tz_to = pytz.timezone(arg2)
                    tm = tz_from.localize(parse(arg3))
                except ValueError:
                    return
        except pytz.UnknownTimeZoneError as e:
            if str(e).lower() == "'blizzard'":
                irc.reply("Blizzard time: Soon™")
            else:
                irc.reply("Unknown time zone " + str(e))
            return
        tm_to = tm.astimezone(tz_to)
        irc.reply(tm_to.strftime("%d %b %H:%M:%S (%Z %z)"))
    tz = wrap(tz, ['something', 'something', optional('text')])

    def rules(self, irc, msg, args, victim):
        """[/37nick]
        Shows the rules for #diablo and #bazaar. If \37nick is specificed (requires op), tells the rules to that user.
        """
        if victim:
            #if not irc.state.channels["#diablo"].isOp(msg.nick):
            #    irc.reply("Only operators can tell rules to others.", private=True)
            #    return
            irc.reply("This message was triggered by %s" % msg.nick, private=True, to=victim)
        else:
            victim = msg.nick
        for v in DiabloCommon.channel_rules:
            irc.reply(v, private=True, to=victim)
    rules = wrap(rules, [optional('nick')])

    def streams(self, irc, msg, args):
        """
        Displays active Diablo streams on twitch.tv.
        """
        if time.time() - DiabloBasic._dstream_time > 600:    #ten minutes
            DiabloBasic._dstream_time = time.time()
            h = httplib2.Http(".cache")
            resp, j = h.request("http://api.justin.tv/api/stream/list.json?meta_game=Diablo%20III", "GET")
            DiabloBasic._dstream_json = json.loads(j)
            resp, j = h.request("http://api.justin.tv/api/stream/list.json?meta_game=Diablo%20II", "GET")
            DiabloBasic._dstream_json.extend(json.loads(j))
            resp, j = h.request("http://api.justin.tv/api/stream/list.json?meta_game=Diablo", "GET")
            DiabloBasic._dstream_json.extend(json.loads(j))
            DiabloBasic._dstream_json = sorted(DiabloBasic._dstream_json, key=lambda x: 0 if x["channel"]["title"] in DiabloBasic._dstream_regulars else 1)

        irc.reply("Active Diablo streams on twitch.tv or justin.tv:", private=True)

        for i in DiabloBasic._dstream_json[:8]:
            irc.reply("%s - %s (%s)" % \
                      (i["channel"]["channel_url"].encode("utf-8"), i["title"].encode("utf-8"),
                       i["meta_game"].encode("utf-8")), private=True)

        if len(DiabloBasic._dstream_json) > 8:
            irc.reply("And %d more!" % (len(DiabloBasic._dstream_json) - 8), private=True)

    streams = wrap(streams)

    def timeleft(self, irc, msg, args):
        """
        Shows the time remaining until the next big event. Only usable by +v or +o.
        """
        if not irc.isChannel(msg.args[0]):
            return
        if not (irc.state.channels[msg.args[0]].isOp(msg.nick) or
                irc.state.channels[msg.args[0]].isVoice(msg.nick)):
            return
        secs = int(1337065200 - time.time()) # 15 May 2012 00:00:00 PDT
        days = secs / 86400
        secs -= days * 86400
        hours = secs / 3600
        secs -= hours * 3600
        mins = secs / 60
        secs -= mins * 60
        irc.reply("Diablo III release: %d days, %d hours, %d minutes, %d seconds" % (days, hours, mins, secs), prefixNick=False)  # 15 May 2012 00:00:00 PDT
    timeleft = wrap(timeleft)

Class = DiabloBasic
