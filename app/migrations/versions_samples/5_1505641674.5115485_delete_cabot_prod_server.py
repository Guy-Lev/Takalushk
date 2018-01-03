"""delete cabot prod server

Revision ID: 5_1505641674.5115485
Revises: 4_1505641524.0353575
Create Date: 2017-09-17 12:47:55.014684

"""
from alembic import op

# revision identifiers, used by Alembic.
from app.models.schema import Server

revision = '5_1505641674.5115485'
down_revision = '4_1505641524.0353575'
branch_labels = None
depends_on = None


data = [{"name": "cabot-prod", "ip": "192.167.168.169"}
        ]
def upgrade():
    op.model_delete(Server, data)


def downgrade():
    pass
