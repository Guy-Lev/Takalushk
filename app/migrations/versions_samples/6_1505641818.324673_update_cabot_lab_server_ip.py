"""update cabot lab server ip

Revision ID: 6_1505641818.324673
Revises: 5_1505641674.5115485
Create Date: 2017-09-17 12:50:18.834021

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
from app.models.schema import Server

revision = '6_1505641818.324673'
down_revision = '5_1505641674.5115485'
branch_labels = None
depends_on = None


data = [{"update_cols": {"ip": "192.167.168.100"}, "key": {"name": "cabot-lab", "ip": "192.167.168.163"}},
        ]

def upgrade():
    op.model_update(Server, data)


def downgrade():
    pass