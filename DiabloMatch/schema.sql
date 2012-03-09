CREATE TABLE users (
	id INTEGER PRIMARY KEY,
	bt TEXT default '',
	reddit_name TEXT default '',
	email TEXT default '',
	irc_name TEXT default '',
	steam_name TEXT default '',
	pass TEXT default '',
	cmt TEXT default '',
	tz INTEGER default 0,
	url TEXT default ''
);
