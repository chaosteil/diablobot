import supybot.ircmsgs as ircmsgs
import time

whois = {}

op_ids = [  #note lowercase
    "maxlemon", "lemonegro",
    "chaosteil",
    "listen2",
    "nitesmoke",
    "onebit",
    "xiphirx_", "xiphirx",
    "thunderclaww",
    "anime",
    "taffing", "taffer"
    ]

channel_rules = [
    "All topics are allowed, but Diablo should always take precedence.",
    "Be polite and respectful of others.",
    "Do not disrupt conversation with spam or bot activities.",
    "Use #bazaar for item trading discussion.",
    "Do not sell, offer to sell, or seek sale of beta keys.",
    "Follow instructions given by the channel operators.",
    "Abide by the EsperNet Charter and Acceptable Use Policy (http://esper.net/charter.php)",
    "See http://bit.ly/wEkLDN for more details."
    ]


def get_services_account(irc, nick):
    # Is nick in Whois?
    if nick not in whois.keys():
        irc.queueMsg(ircmsgs.whois(nick, nick))
        whois[nick] = None    #None means whois in process
        return (1, )
        
    # Whois in progress
    elif whois[nick] == None:
        return (2, )

    # User not authenticated with NickServ
    elif whois[nick] == -1:
        # We try to refresh the auth , maybe the user is registered now
        irc.queueMsg(ircmsgs.whois(nick, nick))
        return (3, )

    # User authenticated some time ago
    else:    
        # Ten hours since auth, we refresh the auth
        if time.time() - whois[nick][1] > 36000:
            irc.queueMsg(ircmsgs.whois(nick, nick))
            return (4, whois[nick][0])

        # User logged in
        else:
            return (5, whois[nick][0])

def check_auth(irc, nick):
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
