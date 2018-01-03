"""insert production cabot

Revision ID: 7_1505645420.041564
Revises: 6_1505641818.324673
Create Date: 2017-09-17 13:50:20.546101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7_1505645420.041564'
down_revision = '6_1505641818.324673'
branch_labels = None
depends_on = None


from alembic import op

from app.models.schema import Server

data = [{"name": "cabot-prod", "ip": "192.167.168.169"}]

def upgrade():
    op.model_insert(Server,data)

def downgrade():
    op.model_delete(Server,data)