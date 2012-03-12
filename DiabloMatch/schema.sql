CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    bt TEXT default NULL,
    reddit_name TEXT default NULL UNIQUE,
    email TEXT default NULL,
    irc_name TEXT default NULL UNIQUE,
    steam_name TEXT default NULL,
    password TEXT default NULL,
    cmt TEXT default NULL,
    tz TEXT default NULL,
    realm TEXT default NULL,
    url TEXT default NULL
);
