# File: alembic/versions/[timestamp]_finalize_permission_changes.py

"""finalize permission changes

Revision ID: b1234567890a
Revises: 835ae3212e16
Create Date: 2024-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'b1234567890a'
down_revision = '835ae3212e16'
branch_labels = None
depends_on = None

def upgrade():
    # Since we made the changes manually, we just need this migration
    # to record that the changes were made
    pass

def downgrade():
    pass