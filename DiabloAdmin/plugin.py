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
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks

import os

class DiabloAdmin(callbacks.Plugin):
    """Add the help for "@plugin help DiabloAdmin" here
    This should describe *how* to use this plugin."""

    def gitpull(self, irc, msg, args, charname):
        """[\37character]
        Returns a random quote from \37character, or from a random character if none is specified.
        """
        if not ircdb.checkCapability(msg.prefix, "owner"):
            irc.reply("Insufficient permissions.")
            return
        os.system("cd /home/diablobot/dbot; git pull")
        irc.reply("Done.")
    gitpull = wrap(gitpull, [optional('lowered')])


Class = DiabloAdmin
