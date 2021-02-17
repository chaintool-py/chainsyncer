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
