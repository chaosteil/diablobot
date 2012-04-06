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
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks

import os, subprocess, sys

if "/home/listen2/dbot/plugins/DiabloCommon" not in sys.path:
     sys.path.append("/home/listen2/dbot/plugins/DiabloCommon")
import DiabloCommon

class DiabloAdmin(callbacks.Plugin):
    """Add the help for "@plugin help DiabloAdmin" here
    This should describe *how* to use this plugin."""
    public = False

    def gitpull(self, irc, msg, args):
        """
        Pulls the latest revision of the git repository from the servers
        """
        os.chdir("/home/listen2/dbot/plugins")
        oldhead = subprocess.Popen(["git", "log -1 --format='%H'"], stdout=subprocess.PIPE).communicate()[0]
        ret = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()[0]
        for f in ret.split("\n"):
            if f == "":
                return
            irc.reply(f, prefixNick=False)
        log = subprocess.Popen(["git", "log --oneline " + oldhead + "..HEAD"], stdout=subprocess.PIPE).communicate()[0]
        for f in log.split("\n"):
            if f == "":
                return
            irc.reply(f, prefixNick=False)
        os.chdir("/home/listen2/dbot/")
    gitpull = wrap(gitpull, [('checkCapability', 'owner')])

    def showlog(self, irc, msg, args):
        """
        Shows the last 5 lines in the error log.
        """
        ret = subprocess.Popen(["tail", "logs/messages.log"], stdout=subprocess.PIPE).communicate()[0]
        irc.reply(ret, private=True)
    showlog = wrap(showlog, [('checkCapability', 'owner')])

    def diablosource(self, irc, msg, args):
        """
        Gives you the current location of the diablobot plugin source code.
        """
        irc.reply("Current location of the supybot plugins for diablobot: "
                  "http://www.github.com/Chaosteil/diablobot")
    diablosource = wrap(diablosource)

    def fixwd(self, irc, msg, args):
        """
        Fix the bot's working directory.
        """
        os.chdir("/home/listen2/dbot/")
        irc.reply(os.getcwd())
    fixwd = wrap(fixwd, [('checkCapability', 'owner')])

Class = DiabloAdmin
