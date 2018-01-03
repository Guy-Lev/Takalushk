"""insert new server to servers table

Revision ID: 4_1505641524.0353575
Revises: 3_1505641398.7807858
Create Date: 2017-09-17 12:45:24.550416

"""

# revision identifiers, used by Alembic.
revision = '4_1505641524.0353575'
down_revision = '3_1505641398.7807858'
branch_labels = None
depends_on = None

from alembic import op

from app.models.schema import Server

data = [{"name": "cabot-prod", "ip": "192.167.168.169"},
        {"name": "cabot-lab", "ip": "192.167.168.163"}]
def upgrade():
    op.model_insert(Server,data)

def downgrade():
    op.model_delete(Server,data)

