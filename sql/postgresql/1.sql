DROP TABLE chain_sync;
CREATE TABLE IF NOT EXISTS chain_sync (
	id serial primary key not null,
	blockchain varchar not null,
	block_start int not null default 0,
	tx_start int not null default 0,
	block_cursor int not null default 0,
	tx_cursor int not null default 0,
	flags bytea not null,
	num_flags int not null,
	block_target int default null,
	date_created timestamp not null,
	date_updated timestamp default null
);

DROP TABLE chain_sync_filter;
CREATE TABLE IF NOT EXISTS chain_sync_filter (
	id serial primary key not null,
	chain_sync_id int not null,
	flags bytea default null,
	count int not null default 0,
	digest char(64) not null default '0000000000000000000000000000000000000000000000000000000000000000',
	CONSTRAINT fk_chain_sync
		FOREIGN KEY(chain_sync_id)
			REFERENCES chain_sync(id)
);
