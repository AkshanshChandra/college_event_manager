"""add payment_method to registrations

Revision ID: a1b2c3d4e5f6
Revises: 904dcd04feab
Create Date: 2026-09-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '904dcd04feab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    payment_method = sa.Enum('online', 'cash', name='paymentmethod')
    payment_method.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'registrations',
        sa.Column(
            'payment_method',
            payment_method,
            server_default='online',
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('registrations', 'payment_method')
    sa.Enum(name='paymentmethod').drop(op.get_bind(), checkfirst=True)
