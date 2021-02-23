from alembic import op
import sqlalchemy as sa

def chainsyncer_upgrade(major, minor, patch):
    r0_0_1_u()

def chainsyncer_downgrade(major, minor, patch):
    r0_0_1_d()

def r0_0_1_u():
    op.create_table(
            'chain_sync',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('blockchain', sa.String, nullable=False, unique=True),
            sa.Column('block_start', sa.Integer, nullable=False, default=0),
            sa.Column('tx_start', sa.Integer, nullable=False, default=0),
            sa.Column('block_cursor', sa.Integer, nullable=False, default=0),
            sa.Column('tx_cursor', sa.Integer, nullable=False, default=0),
            sa.Column('block_target', sa.Integer, nullable=True),
            sa.Column('date_created', sa.DateTime, nullable=False),
            sa.Column('date_updated', sa.DateTime),
            )

    op.create_table(
            'chain_sync_filter',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('chain_sync_id', sa.Integer, sa.ForeignKey('chain_sync.id'), nullable=True),
            sa.Column('flags', sa.BLOB, nullable=True),
            sa.Column('flags_start', sa.BLOB, nullable=True),
            sa.Column('count', sa.Integer, nullable=False, default=0),
            sa.Column('digest', sa.BLOB, nullable=False),
            )

def r0_0_1_d():
    op.drop_table('chain_sync_filter')
    op.drop_table('chain_sync')
