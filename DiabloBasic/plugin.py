# -*- coding: utf-8 -*-
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
import pytz, time
from datetime import datetime
from dateutil.parser import parse
import urllib2

import sys
if "/home/diablobot/dbot/plugins/DiabloCommon" not in sys.path:
     sys.path.append("/home/diablobot/dbot/plugins/DiabloCommon")
import DiabloCommon

class DiabloBasic(callbacks.Plugin):
    """Add the help for "@plugin help DiabloBasic" here
    This should describe *how* to use this plugin."""
    #threaded = True

    # Skill Info
    hash_base = "aZbYcXdWeVfUgThSiRjQkPlOmNnMoLpKqJrIsHtGuFvEwDxCyBzA0123456789+/"
    classes = [
        "barbarian",
        "demon-hunter",
        "monk",
        "witch-doctor",
        "wizard",
        "follower"
    ]
    classes_pretty = {
        "barbarian": "Barbarian",
        "demon-hunter": "Demon Hunter",
        "monk": "Monk",
        "witch-doctor": "Witch Doctor",
        "wizard": "Wizard",
        "follower": "Follower"
    }
    skilldata = {}

    # Stream Info
    _dstream_regulars = [
        "rdiablo",
        "DrZealotTV"
    ]
    _dstream_regulars_json = {}
    _dstream_re = re.compile("diablo", re.IGNORECASE)

    def __init__(self, irc):
        super(DiabloBasic, self).__init__(irc)

        # Load class data
        for c in self.classes:
            with open("plugins/DiabloBasic/data/"+c+".json", "r") as f:
                self.skilldata[c] = json.load(f)

        # Load quotes
        with open("plugins/DiabloBasic/data/quotes.json", "r") as f:
            self.quotes = json.load(f)
        self.quote_count = 0
        for c in self.quotes.values():
            self.quote_count += len(c["quotes"])
        
        # Init stream checking
        DiabloBasic._dstream_time = 0

    def _quotehelp(self):
        return 'Available quote sources: %s (%d quotes)' % \
                (', '.join(sorted(self.quotes.keys())), self.quote_count)

    def printQuote(self, irc, name, message):
        irc.reply("%s: %s" % (name, message), prefixNick=False)

    def quote(self, irc, msg, args, charname):
        """[\37character]
        Returns a random quote from \37character, or from a random character if none is specified.
        """
        # Lists all available quotes
        if charname == "list":
            irc.reply(self._quotehelp())

        # Picks a random quote
        elif not charname:
            # this won't show up in the list of quote sources. it's a secret!
            if random.randrange(0, 999) == 0:
                self.printQuote(irc, "Cow", "Mooooooo! Moo moo moo moo moo!")
            else:
                q = self.quotes[random.choice(self.quotes.keys())]
                self.printQuote(irc, q["name"], random.choice(q["quotes"]))

        # Help text
        elif charname not in self.quotes:
            irc.reply("I don't have any quotes from %s. To get a full list"
                      "of the quotes, enter !quote list" % charname)

        # Prints a quote of the character
        else:
            q = self.quotes[charname]
            self.printQuote(irc, q["name"], random.choice(q["quotes"]))

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
                    for f in self._hash_decode(m.group(2)):    #skills
                        sk.append(self.skilldata[m.group(1)]["skills"][f])
                    out = self.classes_pretty[m.group(1)] + ": "
                    for (n, f) in enumerate(self.hash_decode(m.group(4))):    #runes
                        if f < 0:
                            out += sk[n]["name"] + " (none)"
                        else:
                            out += sk[n]["name"] + " (" + sk[n]["runes"][f]["name"] + ")"
                        out += ", "
                    out = out[:-2]
                    out += " / "
                    for f in self._hash_decode(m.group(3)):    #traits
                        out += self.skilldata[m.group(1)]["traits"][f]["name"] + ", "
                    out = out[:-2]
                    irc.reply(out, prefixNick=False)

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
                    try:
                        tz_from = pytz.timezone("America/Los_Angeles")
                        tm = parse(arg2).replace(tzinfo=tz_from)
                    except ValueError:
                        return
            else:
                try:
                    tz_from = pytz.timezone(arg1)
                    tz_to = pytz.timezone(arg2)
                    tm = parse(arg3).replace(tzinfo=tz_from)
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
    tz = wrap(tz, ['anything', 'anything', optional('text')])

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
        irc.reply("Channel rules for #diablo and #bazaar", private=True)
        for n, v in enumerate(rs):
            irc.reply("%d. %s" % (n+1, v), private=True)
        irc.reply("End of rules", private=True)
    #rules = wrap(rules)

    def streams(self, irc, msg, args, sname):
        """[<\37stream> ...]

        Displays whether \37stream is currently live. If no stream is specified, it lists the status of all the regular streams.
        """
        if time.time() - DiabloBasic._dstream_time > 600:    #ten minutes
            DiabloBasic._dstream_time = time.time()
            j = urllib2.urlopen("http://api.justin.tv/api/stream/search/diablo.json?limit=8")
            DiabloBasic._dstream_json = json.load(j)
            for f in DiabloBasic._dstream_regulars:
                j = urllib2.urlopen("http://api.justin.tv/api/stream/list.json?channel="+f)
                DiabloBasic._dstream_regulars_json[f] = json.load(j)

        irc.reply("Active Diablo streams on twitch.tv or justin.tv:", private=True)
        for f in DiabloBasic._dstream_regulars_json.values():
            if f != [] and DiabloBasic._dstream_re.match(f[0]["meta_game"]):
                irc.reply(f[0]["channel"]["channel_url"] + " - " + f[0]["title"] + " (" + f[0]["meta_game"] + ")", private=True)
        i = 0
        for c in DiabloBasic._dstream_json:
            if i >= 8:
                irc.reply("And more!", private=True)
                return
            try:
                if DiabloBasic._dstream_re.match(c["meta_game"]):
                    irc.reply(c["channel"]["channel_url"] + " - " + c["title"] + " (" + c["meta_game"] + ")", private=True)
                    i += 1
            except:
                pass

    streams = wrap(streams, [optional('anything')])

Class = DiabloBasic
