from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from typing import List
import json

from apps.shared.db import SessionLocal, engine
from apps.shared import models
from apps.shared.schema import (
    TenantCreate,
    FlowCreate,
    InboundMessage,
    ConversationOut,
    MessageOut,
    AssignAgent,
)
from apps.shared.settings import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="WABA Flow API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_queue():
    redis = Redis.from_url(settings.redis_url)
    return Queue("events", connection=redis)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/tenants")
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    tenant = models.Tenant(name=payload.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return {"id": tenant.id, "name": tenant.name}


@app.post("/api/flows")
def create_flow(payload: FlowCreate, db: Session = Depends(get_db)):
    flow = models.Flow(
        tenant_id=payload.tenant_id,
        name=payload.name,
        definition=payload.definition,
        status=payload.status,
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return {"id": flow.id}


@app.post("/webhook/whatsapp")
def whatsapp_webhook(event: InboundMessage, queue=Depends(get_queue)):
    job = queue.enqueue(
        "apps.worker.worker.handle_inbound_message",
        event.model_dump(),
    )
    return {"queued": True, "job_id": job.id}


@app.post("/api/dev/simulate")
def simulate_inbound(event: InboundMessage, queue=Depends(get_queue)):
    job = queue.enqueue(
        "apps.worker.worker.handle_inbound_message",
        event.model_dump(),
    )
    return {"queued": True, "job_id": job.id}


@app.get("/api/inbox/conversations", response_model=List[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    items = db.query(models.Conversation).order_by(models.Conversation.updated_at.desc()).all()
    return items


@app.get("/api/inbox/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def list_messages(conversation_id: int, db: Session = Depends(get_db)):
    items = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
    return items


@app.post("/api/inbox/conversations/{conversation_id}/assign")
def assign_agent(conversation_id: int, payload: AssignAgent, db: Session = Depends(get_db)):
    convo = db.query(models.Conversation).get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo.assigned_agent = payload.agent
    db.commit()
    return {"ok": True}


@app.get("/inbox", response_class=HTMLResponse)
def inbox():
    # Minimal inbox UI served directly by the API
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>WABA Flow Inbox</title>
  <style>
    body { font-family: ui-sans-serif, system-ui; margin: 20px; }
    .layout { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }
    .list { border: 1px solid #ddd; height: 80vh; overflow: auto; }
    .item { padding: 8px 12px; border-bottom: 1px solid #eee; cursor: pointer; }
    .item:hover { background: #fafafa; }
    .details { border: 1px solid #ddd; padding: 12px; height: 80vh; overflow: auto; }
    .msg { margin: 6px 0; }
    .out { color: #0a5; }
    .in { color: #05a; }
  </style>
</head>
<body>
  <h2>Inbox</h2>
  <div class="layout">
    <div class="list" id="list"></div>
    <div class="details" id="details">Select a conversation</div>
  </div>
<script>
async function loadConvos() {
  const res = await fetch('/api/inbox/conversations');
  const data = await res.json();
  const list = document.getElementById('list');
  list.innerHTML = '';
    data.forEach(c => {
    const el = document.createElement('div');
    el.className = 'item';
    el.textContent = `#${c.id} - ${c.participant || 'unknown'} - ${c.state} - ${c.assigned_agent || 'unassigned'}`;
    el.onclick = () => loadMessages(c.id);
    list.appendChild(el);
  });
}
async function loadMessages(id) {
  const res = await fetch(`/api/inbox/conversations/${id}/messages`);
  const msgs = await res.json();
  const details = document.getElementById('details');
  details.innerHTML = `<h3>Conversation #${id}</h3>`;
  msgs.forEach(m => {
    const el = document.createElement('div');
    el.className = 'msg ' + (m.direction === 'outbound' ? 'out' : 'in');
    el.textContent = `${m.direction}: ${m.content}`;
    details.appendChild(el);
  });
}
loadConvos();
setInterval(loadConvos, 5000);
</script>
</body>
</html>
    """
    return HTMLResponse(html)
