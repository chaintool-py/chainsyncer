from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
            'chain_sync_tx',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('blockchain', sa.String, nullable=False),
            sa.Column('chain_sync_id', sa.Integer, sa.ForeignKey('chain_sync.id'), nullable=False),
            sa.Column('flags', sa.LargeBinary, nullable=True),
            sa.Column('block', sa.Integer, nullable=False),
            sa.Column('tx', sa.Integer, nullable=False),
            )

def downgrade():
    op.drop_table('chain_sync_tx')
