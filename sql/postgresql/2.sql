DROP TABLE IF EXISTS chain_sync_filter;
CREATE TABLE IF NOT EXISTS chain_sync_filter (
	id serial primary key not null,
	chain_sync_id integer not null,
	flags bytea default null,
	flags_start bytea default null,
	count integer not null default 0,
	digest bytea not null,
	CONSTRAINT fk_chain_sync
		FOREIGN KEY(chain_sync_id)
			REFERENCES chain_sync(id)
);
