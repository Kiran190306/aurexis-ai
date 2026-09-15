"""Update default model from gpt-4-turbo-preview to gpt-4o-mini

Revision ID: 20260915_0000
Revises: a48ed7b61d7f
Create Date: 2026-09-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260915_0000'
down_revision = 'a48ed7b61d7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update default model in conversations table
    op.execute(
        "UPDATE conversations SET model = 'gpt-4o-mini' WHERE model = 'gpt-4-turbo-preview'"
    )

    # Update default model in user_settings table (users table does not have default_model)
    op.execute(
        "UPDATE user_settings SET default_model = 'gpt-4o-mini' WHERE default_model = 'gpt-4-turbo-preview'"
    )

    # Update default model in agents table
    op.execute(
        "UPDATE agents SET model = 'gpt-4o-mini' WHERE model = 'gpt-4-turbo-preview'"
    )

    # Update default model in prompt_templates table
    op.execute(
        "UPDATE prompt_templates SET default_model = 'gpt-4o-mini' WHERE default_model = 'gpt-4-turbo-preview'"
    )


def downgrade() -> None:
    # Revert to gpt-4-turbo-preview
    op.execute(
        "UPDATE conversations SET model = 'gpt-4-turbo-preview' WHERE model = 'gpt-4o-mini'"
    )

    op.execute(
        "UPDATE user_settings SET default_model = 'gpt-4-turbo-preview' WHERE default_model = 'gpt-4o-mini'"
    )

    op.execute(
        "UPDATE agents SET model = 'gpt-4-turbo-preview' WHERE model = 'gpt-4o-mini'"
    )

    op.execute(
        "UPDATE prompt_templates SET default_model = 'gpt-4-turbo-preview' WHERE default_model = 'gpt-4o-mini'"
    )
