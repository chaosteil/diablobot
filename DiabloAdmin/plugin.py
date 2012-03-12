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

    def gitpull(self, irc, msg, args):
        """[\37gitpull]
        Pulls the latest revision of the git repository from the servers
        """
        os.chdir("/home/diablobot/dbot/plugins")
        ret = os.system("git pull")
        irc.reply("Done. git exit status = " + str(ret))
        os.chdir("/home/diablobot/dbot/")
    gitpull = wrap(gitpull, [('checkCapability', 'owner')])

    def diablosource(self, irc, msg, args):
        """[\37source]
        Gives you the current location of the diablobot model source code.
        """
        irc.reply("http://www.github.com/Chaosteil/diablobot")

    diablosource = wrap(diablosource)

Class = DiabloAdmin
