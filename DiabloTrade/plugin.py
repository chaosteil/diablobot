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

import json, httplib2

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.callbacks as callbacks
import supybot.schedule as schedule

import sys
if "/srv/bots/dbot/plugins/DiabloCommon" not in sys.path:
     sys.path.append("/srv/bots/dbot/plugins/DiabloCommon")
import DiabloCommon

class DiabloTrade(callbacks.Plugin):
    """Add the help for "@plugin help DiabloTrade" here
    This should describe *how* to use this plugin."""

    def __init__(self, irc):
        super(DiabloTrade, self).__init__(irc)

        self._h = httplib2.Http(".cache")
        self._last_listing = None
        self._irc = irc

        try:
            schedule.removeEvent("d3tcheck")
        except KeyError:
            pass #it's okay if the event doesn't exist. Just want to make sure we don't have duplicate events.
        schedule.addPeriodicEvent(self._checklistings, 300, name="d3tcheck", now=True)

    def _checklistings(self):
        """
        Checks for new listings on /r/d3t and prints them to #bazaar
        """
        irc = self._irc #workaround for not being able to pass irc in through addPeriodicEvent() in __init__()

        resp, j = self._h.request(("http://www.reddit.com/r/D3T/new/.json?sort=new&limit=4%s" % ("&before=%s" % (self._last_listing) if self._last_listing else "")), "GET")
        posts = json.loads(j.decode("utf-8"))

        for p in reversed(posts["data"]["children"]):
            irc.reply("New listing by %s: %s (http://reddit.com/r/d3t/comments/%s)" % (p["data"]["author"], p["data"]["title"], p["data"]["id"]), to="#bazaar")
            #TODO if reddit_name is associated with a bt, show the bt
            self._last_listing = "t3_" + p["data"]["id"]

Class = DiabloTrade
