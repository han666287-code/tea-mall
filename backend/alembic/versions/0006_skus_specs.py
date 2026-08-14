"""skus and specs

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_specs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id", "name", name="uq_product_specs_product_name"
        ),
    )
    op.create_index(
        op.f("ix_product_specs_product_id"),
        "product_specs",
        ["product_id"],
        unique=False,
    )
    op.create_table(
        "product_spec_values",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("spec_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["spec_id"], ["product_specs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "spec_id", "value", name="uq_product_spec_values_spec_value"
        ),
    )
    op.create_index(
        op.f("ix_product_spec_values_spec_id"),
        "product_spec_values",
        ["spec_id"],
        unique=False,
    )
    op.create_table(
        "skus",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("sku_code", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("spec_signature", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("price >= 0", name="ck_skus_price_non_negative"),
        sa.CheckConstraint("stock >= 0", name="ck_skus_stock_non_negative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id", "sku_code", name="uq_skus_product_sku_code"
        ),
        sa.UniqueConstraint(
            "product_id",
            "spec_signature",
            name="uq_skus_product_spec_signature",
        ),
    )
    op.create_index(op.f("ix_skus_product_id"), "skus", ["product_id"], unique=False)
    op.create_table(
        "sku_spec_values",
        sa.Column("sku_id", sa.Integer(), nullable=False),
        sa.Column("spec_value_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["spec_value_id"], ["product_spec_values.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("sku_id", "spec_value_id"),
    )
    op.create_index(
        op.f("ix_sku_spec_values_spec_value_id"),
        "sku_spec_values",
        ["spec_value_id"],
        unique=False,
    )

    # 存量商品回填默认 SKU（price/stock 取自原商品字段，数据零删除零回填）
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, price, stock FROM products")).fetchall()
    for row in rows:
        bind.execute(
            sa.text(
                "INSERT INTO skus "
                "(product_id, sku_code, price, stock, spec_signature, is_active, created_at, updated_at) "
                "VALUES (:product_id, :sku_code, :price, :stock, '', 1, now(), now())"
            ),
            {
                "product_id": row[0],
                "sku_code": f"DEFAULT-{row[0]}",
                "price": row[1],
                "stock": row[2],
            },
        )


def downgrade() -> None:
    op.drop_table("sku_spec_values")
    op.drop_table("skus")
    op.drop_table("product_spec_values")
    op.drop_table("product_specs")
