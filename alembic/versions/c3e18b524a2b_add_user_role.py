from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3e18b524a2b"
down_revision: Union[str, None] = "35fe52c3b80a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ENUM type
    userrole_enum = sa.Enum("USER", "MODERATOR", "ADMIN", name="userrole")
    userrole_enum.create(op.get_bind())

    # Add column with default
    op.add_column(
        "users", sa.Column("role", userrole_enum, nullable=False, server_default="USER")
    )

    # Optional: remove server_default after adding if not needed anymore
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
    op.execute("DROP TYPE userrole")
