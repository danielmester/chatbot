from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class TenantCreate(BaseModel):
    name: str


class FlowCreate(BaseModel):
    tenant_id: int
    name: str
    definition: Dict[str, Any]
    status: str = "published"


class InboundMessage(BaseModel):
    tenant_id: int
    from_number: str
    text: str


class ConversationOut(BaseModel):
    id: int
    tenant_id: int
    participant: str | None = None
    state: str
    current_node: Optional[str]
    assigned_agent: Optional[str]


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    direction: str
    content: str


class AssignAgent(BaseModel):
    agent: str
