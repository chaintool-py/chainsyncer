from alembic import op
import sqlalchemy as sa

from chainsyncer.db.migrations.default.versions.src.sync import (
    upgrade as upgrade_sync,
    downgrade as downgrade_sync,
)

from chainsyncer.db.migrations.default.versions.src.sync_tx import (
    upgrade as upgrade_sync_tx,
    downgrade as downgrade_sync_tx,
)

def chainsyncer_upgrade(major=0, minor=0, patch=3):
    r0_0_1_u()
    if patch >= 3:
        r0_0_3_u()

def chainsyncer_downgrade(major=0, minor=0, patch=3):
    if patch >= 3:
        r0_0_3_d()
    r0_0_1_d()

def r0_0_1_u():
    upgrade_sync()

def r0_0_1_d():
    downgrade_sync()


# 0.0.3

def r0_0_3_u():
    upgrade_sync_tx()
 
def r0_0_3_d():
    downgrade_sync_tx()
