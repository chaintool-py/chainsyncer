"""sync-tx

Revision ID: a2ce6826c5eb
Revises: 452ecfa81de3
Create Date: 2021-07-16 18:17:53.439721

"""
# revision identifiers, used by Alembic.
revision = 'a2ce6826c5eb'
down_revision = '452ecfa81de3'
branch_labels = None
depends_on = None

from chainsyncer.db.migrations.default.versions.src.sync_tx import upgrade, downgrade
