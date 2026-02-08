from typing import Dict, Any
from sqlalchemy.orm import Session
from apps.shared.db import SessionLocal, engine
from apps.shared import models

models.Base.metadata.create_all(bind=engine)


def _get_or_create_conversation(db: Session, tenant_id: int, participant: str) -> models.Conversation:
    convo = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.tenant_id == tenant_id,
            models.Conversation.participant == participant,
        )
        .order_by(models.Conversation.updated_at.desc())
        .first()
    )
    if convo:
        return convo
    convo = models.Conversation(tenant_id=tenant_id, participant=participant, state="automated")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def _get_active_flow(db: Session, tenant_id: int) -> models.Flow:
    flow = (
        db.query(models.Flow)
        .filter(models.Flow.tenant_id == tenant_id, models.Flow.status == "published")
        .order_by(models.Flow.version.desc())
        .first()
    )
    if not flow:
        raise ValueError("No published flow found for tenant")
    return flow


def _find_node(definition: Dict[str, Any], node_id: str):
    for node in definition.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def _advance_flow(db: Session, convo: models.Conversation, flow: models.Flow, inbound_text: str | None = None):
    definition = flow.definition
    if not definition.get("nodes"):
        return

    if not convo.current_node:
        convo.current_node = definition["nodes"][0]["id"]

    while convo.current_node:
        node = _find_node(definition, convo.current_node)
        if not node:
            convo.state = "closed"
            convo.current_node = None
            db.commit()
            return

        node_type = node.get("type")
        if node_type == "send_message":
            message = node.get("message", "")
            db.add(models.Message(conversation_id=convo.id, direction="outbound", content=message))
            convo.current_node = node.get("next")
            db.commit()
            continue

        if node_type == "ask_question":
            # If we just received inbound text, store it and move on.
            if inbound_text is not None:
                convo.current_node = node.get("next")
                db.commit()
                inbound_text = None
                continue
            # Otherwise, wait for user input.
            db.add(models.Message(conversation_id=convo.id, direction="outbound", content=node.get("prompt", "")))
            convo.state = "waiting_for_user"
            db.commit()
            return

        if node_type == "end":
            convo.state = "closed"
            convo.current_node = None
            db.commit()
            return

        # Unknown node type: stop safely
        convo.state = "escalated"
        db.commit()
        return


def handle_inbound_message(event: Dict[str, Any]):
    db = SessionLocal()
    try:
        tenant_id = event["tenant_id"]
        participant = event.get("from_number", "unknown")
        text = event.get("text", "")
        convo = _get_or_create_conversation(db, tenant_id, participant)
        db.add(models.Message(conversation_id=convo.id, direction="inbound", content=text))
        db.commit()

        flow = _get_active_flow(db, tenant_id)
        _advance_flow(db, convo, flow, inbound_text=text)
    finally:
        db.close()
