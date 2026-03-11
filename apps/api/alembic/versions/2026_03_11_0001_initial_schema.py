"""Initial schema — all tables, indexes, and pgvector extension.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-11 00:00:00.000000

This migration is the authoritative source for the production Postgres schema.
It is equivalent to running migrations/001_initial_schema.sql directly.
For SQLite (dev/test), Base.metadata.create_all() is used instead.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------
    # Native ENUM types (Postgres only)
    # ------------------------------------------------------------------
    leadstatus = postgresql.ENUM(
        "new", "engaged", "qualified", "closed",
        name="leadstatus", create_type=False,
    )
    leadstatus.create(op.get_bind(), checkfirst=True)

    conversationstate = postgresql.ENUM(
        "intake", "awaiting_follow_up", "escalated", "completed",
        name="conversationstate", create_type=False,
    )
    conversationstate.create(op.get_bind(), checkfirst=True)

    messagedirection = postgresql.ENUM(
        "inbound", "outbound",
        name="messagedirection", create_type=False,
    )
    messagedirection.create(op.get_bind(), checkfirst=True)

    appointmentstatus = postgresql.ENUM(
        "pending", "confirmed", "cancelled",
        name="appointmentstatus", create_type=False,
    )
    appointmentstatus.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # leads
    # ------------------------------------------------------------------
    op.create_table(
        "leads",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("agency_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("source_channel", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("new", "engaged", "qualified", "closed", name="leadstatus"),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_leads_agency_id", "leads", ["agency_id"])

    # ------------------------------------------------------------------
    # conversations
    # ------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "current_state",
            sa.Enum("intake", "awaiting_follow_up", "escalated", "completed", name="conversationstate"),
            nullable=False,
            server_default="intake",
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_conversations_lead_id", "conversations", ["lead_id"])

    # ------------------------------------------------------------------
    # messages
    # ------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "direction",
            sa.Enum("inbound", "outbound", name="messagedirection"),
            nullable=False,
        ),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("provider_message_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index(
        "idx_messages_provider_id",
        "messages",
        ["provider_message_id"],
        postgresql_where=sa.text("provider_message_id IS NOT NULL"),
    )

    # ------------------------------------------------------------------
    # appointments
    # ------------------------------------------------------------------
    op.create_table(
        "appointments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_event_id", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "cancelled", name="appointmentstatus"),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_index("idx_appointments_lead_id", "appointments", ["lead_id"])

    # ------------------------------------------------------------------
    # summaries
    # ------------------------------------------------------------------
    op.create_table(
        "summaries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # ------------------------------------------------------------------
    # audit_events
    # ------------------------------------------------------------------
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("lead_id", sa.BigInteger(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_audit_events_lead_id", "audit_events", ["lead_id"])

    # ------------------------------------------------------------------
    # knowledge_vectors (LlamaIndex PGVectorStore)
    # Managed by LlamaIndex at runtime; created here for completeness.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_vectors (
            id        TEXT PRIMARY KEY,
            text      TEXT NOT NULL,
            metadata_ JSONB NOT NULL DEFAULT '{}',
            node_id   TEXT,
            embedding vector(1536)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_vectors_embedding
        ON knowledge_vectors USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.drop_table("knowledge_vectors")
    op.drop_table("audit_events")
    op.drop_table("summaries")
    op.drop_table("appointments")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("leads")

    op.execute("DROP TYPE IF EXISTS appointmentstatus")
    op.execute("DROP TYPE IF EXISTS messagedirection")
    op.execute("DROP TYPE IF EXISTS conversationstate")
    op.execute("DROP TYPE IF EXISTS leadstatus")
    op.execute("DROP EXTENSION IF EXISTS vector")
