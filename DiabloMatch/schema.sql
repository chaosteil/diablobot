CREATE TABLE users (
	id INTEGER PRIMARY KEY,
	bt TEXT default '',
	reddit_name TEXT default '' UNIQUE,
	email TEXT default '',
	irc_name TEXT default '' UNIQUE,
	steam_name TEXT default '',
	pass TEXT default '',
	cmt TEXT default '',
	tz INTEGER default 0,
	realm TEXT default '',
	url TEXT default ''
);
