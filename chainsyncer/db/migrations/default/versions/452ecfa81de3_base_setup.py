"""base setup

Revision ID: 452ecfa81de3
Revises: 
Create Date: 2021-07-16 16:29:32.460027

"""
# revision identifiers, used by Alembic.
revision = '452ecfa81de3'
down_revision = None
branch_labels = None
depends_on = None

from chainsyncer.db.migrations.default.versions.src.sync import upgrade, downgrade
