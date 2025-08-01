"""empty message

Revision ID: 6b5bfe16338d
Revises: a478975d776b
Create Date: 2025-07-24 09:15:22.653151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b5bfe16338d'
down_revision = 'a478975d776b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('badges', schema=None) as batch_op:
        batch_op.add_column(sa.Column('revoked', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('badges', schema=None) as batch_op:
        batch_op.drop_column('revoked')

    # ### end Alembic commands ###
