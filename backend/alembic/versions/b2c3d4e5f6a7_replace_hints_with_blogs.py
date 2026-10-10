"""replace hints with blogs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# publishstatus already exists (created by the initial migration for
# problem_statements.status) — reuse it, don't try to recreate it.
_publish_status = postgresql.ENUM('draft', 'published', name='publishstatus', create_type=False)


def upgrade() -> None:
    op.create_table(
        'blogs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', _publish_status, server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain_id'),
    )

    op.drop_table('hints')
    sa.Enum(name='hintscope').drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.create_table(
        'hints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('scope', sa.Enum('global', 'domain', name='hintscope'), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('publish_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', _publish_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.drop_table('blogs')
