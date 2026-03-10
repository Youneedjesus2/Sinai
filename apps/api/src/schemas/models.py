from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class LeadStatus(str, Enum):
    new = 'new'
    engaged = 'engaged'
    qualified = 'qualified'
    closed = 'closed'


class ConversationState(str, Enum):
    intake = 'intake'
    awaiting_follow_up = 'awaiting_follow_up'
    escalated = 'escalated'
    completed = 'completed'


class MessageDirection(str, Enum):
    inbound = 'inbound'
    outbound = 'outbound'


class AppointmentStatus(str, Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    cancelled = 'cancelled'


class Lead(Base):
    __tablename__ = 'leads'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agency_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    source_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(SAEnum(LeadStatus), default=LeadStatus.new, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    conversations = relationship('Conversation', back_populates='lead')


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=False)
    current_state: Mapped[ConversationState] = mapped_column(SAEnum(ConversationState), default=ConversationState.intake, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    lead = relationship('Lead', back_populates='conversations')
    messages = relationship('Message', back_populates='conversation')


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey('conversations.id'), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(SAEnum(MessageDirection), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship('Conversation', back_populates='messages')


class Appointment(Base):
    __tablename__ = 'appointments'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=False)
    provider_event_id: Mapped[str | None] = mapped_column(String(120))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[AppointmentStatus] = mapped_column(SAEnum(AppointmentStatus), default=AppointmentStatus.pending, nullable=False)


class Summary(Base):
    __tablename__ = 'summaries'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = 'audit_events'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey('leads.id'), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
