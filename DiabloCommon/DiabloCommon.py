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

import supybot.ircmsgs as ircmsgs
import time

whois = {}

channel_rules = [
    "Channel rules for #diablo and #bazaar",
    "1. All topics are allowed, but Diablo should always take precedence.",
    "2. Be polite and respectful of others.",
    "3. Do not disrupt conversation with spam or bot activities.",
    "4. Use #bazaar for item trading discussion.",
    "5. Do not sell, offer to sell, or seek sale of beta keys.",
    "6. Follow instructions given by the channel operators.",
    "7. Abide by the EsperNet Charter and Acceptable Use Policy (http://esper.net/charter.php)",
    "8. See http://bit.ly/wEkLDN for more details.",
    "End of rules"
    ]


def get_services_account(irc, nick):
    """irc object, nick str
    Returns a tuple (status, name). status indicates whether the nick is logged in to NickServ.
    1: user not seen, 2: WHOIS in progress, 3: user known to be not logged in, 4: user logged in
    but expired, 5: logged in and current.
    The second element of the tuple is None for statuses 1-3 and the NickServ account name for
    statuses 4-5.
    """
    if nick not in whois.keys():
        # user hasn't been seen before
        irc.queueMsg(ircmsgs.whois(nick, nick))
        whois[nick] = None    # None indicates that a WHOIS is in process
        return (1, )

    elif whois[nick] == None:
        # user has been seen but WHOIS did not yet finish
        return (2, )

    elif whois[nick] == -1:
        # user is known, but is not logged in to NickServ
        # we'll check again, in case they have logged in since the last time
        irc.queueMsg(ircmsgs.whois(nick, nick))
        return (3, )

    else:
        # user is known and authenticated
        if time.time() - whois[nick][1] > 36000:
            # but ten hour have passed, so refresh the entry
            irc.queueMsg(ircmsgs.whois(nick, nick))
            return (4, whois[nick][0])

        else:
            # known and authenticated less than ten hours ago
            return (5, whois[nick][0])

def check_auth(irc, nick):
    """irc object, nick str
    Convenient wrapper for get_services_account that notifies the user of what's going on.
    Returns the NickServ account name if the user is logged in and current, otherwise None.
    """
    a = get_services_account(irc, nick)
    if a[0] == 1:
        irc.reply("Sorry, I needed to verify your identity. "
                  "Please repeat your previous command.", private=True)
    elif a[0] == 2:
        irc.reply("Still verifying your identity. "
                  "Try again in a few seconds.", private=True)
    elif a[0] == 3:
        irc.reply("You're not logged in. Please authenticate with "
                  "NickServ so I know who you are.", private=True)
    elif a[0] == 4:
        irc.reply("You were logged in to NickServ as '%s', but your "
                  "last session expired. Please repeat your previous "
                  "command." % a[1], private=True)
    elif a[0] == 5:
        #irc.reply("You're logged in to NickServ as '%s'." % a[1], private=True)
        return a[1]
    else:
        irc.reply("This can't ever happen. "
                  "Someone must have divided by zero.", private=True)
    return False

def timeago(sec):
    """elapsed seconds
    Returns the length of time formatted the way Reddit does.
    """
    sec = (int(sec))
    n = sec / 31536000
    if n:
        return "%d year%s" % (n, "s" if n > 1 else "")
    n = sec / 2592000
    if n:
        return "%d month%s" % (n, "s" if n > 1 else "")
    n = sec / 604800
    if n:
        return "%d week%s" % (n, "s" if n > 1 else "")
    n = sec / 86400
    if n:
        return "%d day%s" % (n, "s" if n > 1 else "")
    n = sec / 3600
    if n:
        return "%d hour%s" % (n, "s" if n > 1 else "")
    n = sec / 60
    if n:
        return "%d minutes%s" % (n, "s" if n > 1 else "")
    return "%d second%s" % (sec, "s" if sec > 1 else "")    
