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

from sqlalchemy import create_engine, Table, MetaData, func, or_
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.sql import expression

import time, pytz
import re
from datetime import datetime
import hashlib
import random

import sys
if "/srv/bots/dbot/plugins/DiabloCommon" not in sys.path:
     sys.path.append("/srv/bots/dbot/plugins/DiabloCommon")
import DiabloCommon

class User(object):
    quickfields = [
        ("irc_name", "IRC"),
        ("reddit_name", "Reddit"),
        ("steam_name", "Steam*"),
        ("bt", "Battletag*")
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return "<User('%s')>" % (self.irc_name)

    def pretty_print(self, r=True):
        out = ", ".join(["" + f[1] + ": " + getattr(self, f[0]) for f in User.quickfields if getattr(self, f[0]) not in [None, 0]])
        if r and self.realm != None:
            out += ", Realm: %s" % (self.realm)
        return out

    def full_print(self):
        out = self.pretty_print(r=False) + " "
        if self.realm != None:
            out += "Realm: %s " % (self.realm)
        if self.tz != None:
            tz_to = pytz.timezone(self.tz)
            tz_from = pytz.timezone("America/Los_Angeles")
            tm = tz_from.localize(datetime.now())
            tm_to = tm.astimezone(tz_to)
            out += "Local time: %s " % (tm_to.strftime("%d %b %H:%M:%S (%Z %z)"))
        if self.cmt != None:
            out += "Comment: %s " % (self.cmt)
        if self.url != None:
            out += "URL: %s " % (self.url)
        return out

class Verification(object):
    def __init__(self):
        pass

    def __repr__(self):
        return "<Verification('%s')>" % (self.id)

class Profile(object):
    def __init__(self):
        pass

    def __repr__(self):
        return "<Profile('%s')>" % (self.id)

#engine = create_engine('sqlite:///plugins/DiabloMatch/db.sqlite3', echo=True)
#engine = create_engine('sqlite:////srv/bots/dbot/plugins/DiabloMatch/db.sqlite3')
f = open('/home/listen2/db_pass', 'r')
p = f.read().rstrip()
f.close()
engine = create_engine("postgresql://rdiablo:"+p+"@127.0.0.1/rdiablo")
Session = sessionmaker(bind=engine)
meta = MetaData()
meta.bind = engine
user_table = Table('users', meta, autoload=True)
mapper(User, user_table)
verification_table = Table('reddit_v', meta, autoload=True)
mapper(Verification, verification_table)
profile_table = Table('profiles', meta, autoload=True)
mapper(Profile, profile_table)

class DiabloMatch(callbacks.Plugin):
    """Add the help for "@plugin help DiabloMatch" here
    This should describe *how* to use this plugin."""

    # TODO fix when the actual list is made available
    _realms = [
        "useast",
        "uswest",
        "europe",
        "asia"
    ]

    _bt_regexp    = re.compile(r"\w{1,32}#\d{4,8}$")
    _color_regexp = re.compile("(?:(?:\d{1,2}(?:,\d{1,2})?)?|||)")
    _bt_lfgargs_regexp = re.compile("(\S+\s*=.+?(?=\s+\S+\s*=|$))")

    # "Logged in as" WHOIS response
    def do330(self, irc, msg):
        nick = msg.args[1]
        account = msg.args[2]
        DiabloCommon.whois[nick] = (account, time.time())

    # End of WHOIS responses
    def do318(self, irc, msg):
        # If we get this and didn't get a 330, then the user is not logged in
        nick = msg.args[1]
        if DiabloCommon.whois[nick] == None:
            DiabloCommon.whois[nick] = -1 #-1 means whois complete and not logged in

    def _btRegister(self, irc, msg, battletag):
        if battletag:
            irc.reply("After registering, use !btset to set your profile fields.", private=True)
            irc.reply("If you set reddit_name, I'll sync your battletag from your /r/diablo flair.", private=True)
            self.btset(irc, msg, ["bt", battletag])
        else:
            irc.reply("Please specify the battletag you wish to register: "
                      "!bt register BattleTag#1234", private=True)

    def _findBtUsers(self, irc, name, typename):
        session = Session()

        datatypes_pretty = {
            "bt":      (User.bt, "BattleTag"),
            "reddit":  (User.reddit_name, "Reddit Username"),
            "email":   (User.email, "Email Address"),
            "irc":     (User.irc_name, "IRC Services Username"),
            "steam":   (User.steam_name, "Steam Username")
        }

        # A small helper closure
        def show_result(datatype, count):
            irc.reply("Looking up user %s (%s). %d result%s. "
                      "Use !btinfo <user> for details." %
                      (name, datatype , count,
                       "s" if not users.count() == 1 else ""),
                     private=True)

        if typename in datatypes_pretty.keys():
            users = session.query(User).filter(
                func.lower(datatypes_pretty[typename][0]).like(
                    func.lower(name.replace("*", "%"))))
            show_result(datatypes_pretty[typename][1], users.count())

        elif typename == None:
            users = session.query(User).filter(or_(
                    func.lower(User.bt).like(
                        func.lower(name.replace("*", "%"))),
                    func.lower(User.reddit_name).like(
                        func.lower(name.replace("*", "%"))),
                    func.lower(User.email).like(
                        func.lower(name.replace("*", "%"))),
                    func.lower(User.irc_name).like(
                        func.lower(name.replace("*", "%"))),
                    func.lower(User.steam_name).like(
                        func.lower(name.replace("*", "%")))))
            show_result("All fields", users.count())

        else:
            irc.reply("I don't recognize that field. Known fields: "
                      "bt, reddit, email, irc, steam",
                      private=True)
            users = []

        return users

    def bt(self, irc, msg, args, arg1, arg2):
        """[\37user]  |  register \37Battletag#1234
        Shows user information. \37user may be prefixed with irc:, steam:, reddit:, email:, or bt:, and may contain the wildcard *. If \37user is not supplied, your own information will be displayed.
        If the first argument is register, the given \37battletag will be registered as yours.
        """

        if arg1 == "register":
            self._btRegister(irc, msg, arg2)
        elif arg1 == None:
            s = DiabloCommon.check_auth(irc, msg.nick)
            if s:
                session = Session()
                try:
                    # We pick one user. irc_name is unique, so no worries
                    user = session.query(User).filter(
                        func.lower(User.irc_name) == func.lower(s)).one()
                    irc.reply("Your battletag is %s" % user.pretty_print(),
                              private=True)

                except NoResultFound:
                    irc.reply("No battletag found for you. Register one with "
                              "!bt register BattleTag#1234", private=True)
        else:
            data = arg1.split(":", 1)

            users = self._findBtUsers(irc, data[-1], None if len(data) == 1 else data[0])

            for user in users[0:6]:
                irc.reply(user.pretty_print(), private=True)

    bt = wrap(bt, [optional('something'), optional('something')])

    def btinfo(self, irc, msg, args, arg1):
        """[\37user]
        Shows detailed user information. \37user may be prefixed with irc:, steam:, reddit:, email:, or bt:, and may contain the wildcard *. If \37user is not supplied, your own information will be displayed.
        """
        if arg1 == None:
            data = ["irc", msg.nick]
        else:
            data = arg1.split(":", 1)

        users = self._findBtUsers(irc, data[-1], "irc" if len(data) == 1 else data[0])

        for user in users[0:10]:
            #irc.reply("User details. Fields marked with a * are not "
            #      "officially validated.", private=True)
            irc.reply(user.full_print(), private=True)

    btinfo = wrap(btinfo, [optional('something')])

    def _check_registered(self, irc, msg, session, ircname):
        try:
            user = session.query(User).filter(
                func.lower(User.irc_name) == func.lower(ircname)).one()
        except NoResultFound:
            irc.reply("Register a battletag first.", private=True)
            return None
        return user

    def btset(self, irc, msg, args, arg1, arg2):
        """\37field \37value
        Modifies your user info. Invoke btset list to see a list of available fields
        """
        try:
            arg1 = DiabloMatch._color_regexp.sub("", arg1)
            arg2 = DiabloMatch._color_regexp.sub("", arg2)
        except:
            pass
        if arg1.lower() == "list":    #or arg1.lower() not in []:
            irc.reply("Available fields: bt/battletag, reddit_name, email, steam_name, password, comment, tz/timezone, realm, url", private=True)
            return
        if arg2 == None:
            irc.reply("Here's the current value of " + arg1 + ": (not yet implemented).", private=True)
            return
        ircname = DiabloCommon.check_auth(irc, msg.nick)
        if not ircname:
            return
        if arg1.lower() in ["bt", "battletag"]:
            if DiabloMatch._bt_regexp.match(arg2) == None:
                irc.reply("That's not a proper battletag. Use 'BattleTag#1234' format.", private=True)
                return
            session = Session()
            try:
                user = session.query(User).filter(func.lower(User.irc_name) == func.lower(ircname)).one()
            except NoResultFound:    #we want irc_name to be unique, even though it's not a primary key
                user = User()
                user.irc_name = ircname
            user.bt = arg2
            session.add(user)
            session.commit()

            irc.reply("Registered your battletag as %s" % arg2,
                      private=True)
        elif arg1.lower() in ["tz", "timezone"]:
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            try:
                pytz.timezone(arg2)
            except pytz.UnknownTimeZoneError as e:
                irc.reply("Unknown time zone %s" % str(e), private=True)
                irc.reply("You can find a list of valid time zones at "
                          "http://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                          private=True)
                return
            user.tz = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set timezone to " + arg2 + ".", private=True)
        elif arg1.lower() == "realm":
            if arg2 not in DiabloMatch._realms:
                irc.reply("That's not a valid realm. Valid realms: " + ", ".join(DiabloMatch._realms) + ".", private=True)
                return
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            user.realm = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set realm to " + arg2 + ".", private=True)
        elif arg1.lower() in ["steam", "steam_name"]:
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            user.steam_name = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set steam_name to " + arg2 + ".", private=True)
        elif arg1.lower() == "password":
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            hasher = hashlib.sha256()
            hasher.update(arg2)
            user.password = expression.null() if arg2 == "" else hasher.hexdigest()
            session.add(user)
            session.commit()
            irc.reply("Set password.", private=True)
        elif arg1.lower() == "email":
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            user.email = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set email address to " + arg2 + ".", private=True)
        elif arg1.lower() == "comment":
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            user.cmt = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set comment to " + arg2 + ".", private=True)
        elif arg1.lower() == "url":
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            user.url = expression.null() if arg2 == "" else arg2
            session.add(user)
            session.commit()
            irc.reply("Set URL to " + arg2 + ".", private=True)
        elif arg1.lower() in ["reddit", "reddit_name"]:
            session = Session()
            user = self._check_registered(irc, msg, session, ircname)
            if user == None:
                return
            try:
                ver = session.query(Verification).filter(Verification.id == user.id).one()
            except NoResultFound:
                ver = Verification()
            ver.id = user.id
            hasher = hashlib.sha256()
            hasher.update(str(random.randint(0, 4294967295)))
            k = hasher.hexdigest()[0:32]
            ver.key = k
            session.add(ver)
            session.commit()
            irc.reply("Send a PM on Reddit to GharbadTheWeak with the subject diablobot verification and the body " + k + "", private=True)
            irc.reply("http://www.reddit.com/message/compose/?to=GharbadTheWeak&subject=diablobot%20verification&message=" + k, private=True)
            irc.reply("Your verification will be accepted within an hour of receipt.", private=True)
    btset = wrap(btset, ['something', optional('text')])

    def btverify(self, irc, msg, args, key):
        """\37profile name
        Verifies your IRC services name. This is only useful if you did not register through IRC.
        """
        ircname = DiabloCommon.check_auth(irc, msg.nick)
        if not ircname:
            return
        session = Session()
        try:
            user = session.query(User).join(Verification).filter(Verification.key == key).one()
        except NoResultFound:
            irc.reply("Key not recognized.", private=True) #TODO better feedback message
            return
        ver = session.query(Verification).filter(Verification.id == user.id).one()
        user.irc_name = ircname
        session.add(user)
        session.delete(ver)
        session.commit()
        irc.reply("Success.", private=True)
    btverify = wrap(btverify, ["something"])

    def lfgset(self, irc, msg, args, pname):
        """\37profile name [\37option=\37value ...]
        Sets options for the profile \37profile name. The profile will be created if it does not exist.
        """
        ircname = DiabloCommon.check_auth(irc, msg.nick)
        if not ircname:
            return
        session = Session()
        if pname:
            try:
                #TODO can we exclude all columns other than default_profile ?
                profile = session.query(Profile).join(User).filter(func.lower(User.irc_name) == func.lower(ircname)).filter(func.lower(Profile.profile_name) == func.lower(pname)).one()
            except NoResultFound:
                irc.reply("You don't have a profile named '%s'." % pname)
                return
        else:
            u = session.query(User).filter(func.lower(User.irc_name) == func.lower(ircname)).one()
            if not u.default_profile:
                irc.reply("You don't have a default profile set. Use !lfgset profile and !btset default_profile to set one.")
                return
            else:
                try:
                    profile = session.query(Profile).join(User).filter(func.lower(User.irc_name) == func.lower(ircname)).filter(func.lower(Profile.profile_name) == func.lower(User.default_profile)).one()
                except NoResultFound:
                    irc.reply("Your default profile '%s' doesn't exist." % pname)
                    return
        irc.reply("Using profile %s" % profile.profile_name)
    lfgset = wrap(lfgset, [optional("text")])

    def lfg(self, irc, msg, args, argv):
        """[\37profile name]
        Finds players that match the game profile \37profile name. If \37profile name is not specified, your default profile is used. Issue !lfgset profile to create or modify profiles.
        """
        ircname = DiabloCommon.check_auth(irc, msg.nick)
        if not ircname:
            return

        ovs = []
        pname = None
        if not argv == None: #Hold on to your butts...
            arg_sp = argv.split(None, 1)      #split off the first word
            if "=" in arg_sp[0]:      #does the first word contain an equals sign?
                arg_ov = argv #yes, so the user is getting right into the overrides
            else:
                if len(arg_sp) > 1 and arg_sp[1].find("=") == 0:      #maybe the second word starts with an equals sign?
                    arg_ov = argv #yes, they're getting right into the overrides.
                else:
                    pname = arg_sp[0] #nope. the first word must be a profile name.
                    try:
                        arg_ov = arg_sp[1]
                    except IndexError:  #there are no args
                        arg_ov = None
            #now pname contains the name of the profile or None, and arg_ov contans the remainder of the string
            if not arg_ov == None:
                for f in DiabloMatch._bt_lfgargs_regexp.findall(arg_ov):
                    p = f.split("=")
                    ovs.append((p[0].strip(), p[1].strip()))
                #now ovs contains the (key, value) of every override specified in argv
        irc.reply("using profile %s with the following overrides: %s" % (pname, ovs))
        return

        session = Session()
        if pname:
            try:
                #TODO can we exclude all columns other than default_profile ?
                profile = session.query(Profile).join(User).filter(func.lower(User.irc_name) == func.lower(ircname)).filter(func.lower(Profile.profile_name) == func.lower(pname)).one()
            except NoResultFound:
                irc.reply("You don't have a profile named '%s'." % pname)
                return
        else:
            u = session.query(User).filter(func.lower(User.irc_name) == func.lower(ircname)).one()
            if not u.default_profile:
                irc.reply("You don't have a default profile set. Use !lfgset profile and !btset default_profile to set one.")
                return
            else:
                try:
                    profile = session.query(Profile).join(User).filter(func.lower(User.irc_name) == func.lower(ircname)).filter(func.lower(Profile.profile_name) == func.lower(User.default_profile)).one()
                except NoResultFound:
                    irc.reply("Your default profile '%s' doesn't exist." % pname)
                    return

        irc.reply("Using profile %s" % profile.profile_name)
    lfg = wrap(lfg, [optional("text")])

    #on any channel activity, cache the user's whois info
    def doPrivmsg(self, irc, msg):
        if ircmsgs.isCtcp(msg) and not ircmsgs.isAction(msg):
            return
        if irc.isChannel(msg.args[0]):
            DiabloCommon.get_services_account(irc, msg.nick)

    #on any channel join, cache the user's whois info
    def doJoin(self, irc, msg):
        if irc.isChannel(msg.args[0]):
            DiabloCommon.get_services_account(irc, msg.nick)

Class = DiabloMatch
