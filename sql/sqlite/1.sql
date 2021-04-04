CREATE TABLE IF NOT EXISTS chain_sync (
	id integer primary key autoincrement,
	blockchain varchar not null,
	block_start integer not null default 0,
	tx_start integer not null default 0,
	block_cursor integer not null default 0,
	tx_cursor integer not null default 0,
	block_target integer default null,
	date_created timestamp not null,
	date_updated timestamp default null
);
