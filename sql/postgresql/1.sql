DROP TABLE IF EXISTS chain_sync CASCADE;
CREATE TABLE IF NOT EXISTS chain_sync (
	id serial primary key not null,
	blockchain varchar not null,
	block_start int not null default 0,
	tx_start int not null default 0,
	block_cursor int not null default 0,
	tx_cursor int not null default 0,
	block_target int default null,
	date_created timestamp not null,
	date_updated timestamp default null
);
