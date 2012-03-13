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

import os, subprocess

# Pulled from http://stackoverflow.com/a/136368
def tail(f, window=20):
    BUFSIZ = 1024
    f.seek(0, 2)
    bytes = f.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (bytes - BUFSIZ > 0):
            # Seek back one whole BUFSIZ
            f.seek(block*BUFSIZ, 2)
            # read BUFFER
            data.append(f.read(BUFSIZ))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            data.append(f.read(bytes))
        linesFound = data[-1].count('\n')
        size -= linesFound
        bytes -= BUFSIZ
        block -= 1
    return '\n'.join(''.join(data).splitlines()[-window:])

class DiabloAdmin(callbacks.Plugin):
    """Add the help for "@plugin help DiabloAdmin" here
    This should describe *how* to use this plugin."""

    def gitpull(self, irc, msg, args):
        """[\37gitpull]
        Pulls the latest revision of the git repository from the servers
        """
        os.chdir("/home/diablobot/dbot/plugins")
        ret = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()[0]
        irc.reply("Done. git exit status = %s" % ret)
        os.chdir("/home/diablobot/dbot/")
    gitpull = wrap(gitpull, [('checkCapability', 'owner')])

    def showlog(self, irc, msg, args):
        """[\37showlog]
        Shows the last 5 lines in the error log.
        """
        ret = subprocess.Popen(["tail", "logs/messages.log"], stdout=subprocess.PIPE).communicate()[0]
        for f in ret.split("\n"):
            irc.reply(f, private=True)
    showlog = wrap(showlog, [('checkCapability', 'owner')])

    def diablosource(self, irc, msg, args):
        """[\37source]
        Gives you the current location of the diablobot plugin source code.
        """
        irc.reply("Current location of the supybot plugins for diablobot: "
                  "http://www.github.com/Chaosteil/diablobot")
    diablosource = wrap(diablosource)

Class = DiabloAdmin
