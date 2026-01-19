"""Create batch analysis tables

Revision ID: 002_add_batch_analysis_tables
Revises: 001_auth_features
Create Date: 2026-01-19 17:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_batch_analysis_tables"
down_revision = "001_auth_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_analysis_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("total_documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "processed_documents", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("granularity", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("similarity_matrix", sa.JSON(), nullable=True),
        sa.Column("clusters", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
    )

    op.create_index(
        op.f("ix_batch_analysis_jobs_user_id"),
        "batch_analysis_jobs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_batch_analysis_jobs_status"),
        "batch_analysis_jobs",
        ["status"],
        unique=False,
    )

    op.create_table(
        "batch_documents",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
        sa.Column("ai_probability", sa.Float(), nullable=True),
        sa.Column("confidence_distribution", sa.JSON(), nullable=True),
        sa.Column("heat_map_data", sa.JSON(), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["batch_analysis_jobs.id"],
        ),
    )

    op.create_index(
        op.f("ix_batch_documents_job_id"),
        "batch_documents",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_batch_documents_status"),
        "batch_documents",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_batch_documents_status"), table_name="batch_documents")
    op.drop_index(op.f("ix_batch_documents_job_id"), table_name="batch_documents")
    op.drop_table("batch_documents")
    op.drop_index(
        op.f("ix_batch_analysis_jobs_status"), table_name="batch_analysis_jobs"
    )
    op.drop_index(
        op.f("ix_batch_analysis_jobs_user_id"), table_name="batch_analysis_jobs"
    )
    op.drop_table("batch_analysis_jobs")
