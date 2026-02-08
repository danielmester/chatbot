from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB
from .db import Base


# Use JSONB when available; SQLite will use a fallback JSON type.
JSONType = JSONB().with_variant(SQLITE_JSON, "sqlite")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Flow(Base):
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="published")
    definition = Column(JSONType, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    participant = Column(String(50), nullable=True, index=True)
    state = Column(String(50), nullable=False, default="automated")
    current_node = Column(String(200), nullable=True)
    assigned_agent = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # inbound/outbound
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    event_type = Column(String(200), nullable=False)
    data = Column(JSONType, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
