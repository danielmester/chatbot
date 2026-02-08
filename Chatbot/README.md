# WABA Flow MVP

Minimal, code-agnostic MVP scaffold for the WABA Flow platform:

- Webhook API (FastAPI)
- Orchestrator worker (RQ)
- Inbox UI (simple HTML in API)
- Postgres + Redis
- Render deployment config

## Local Dev (optional)

```bash
docker compose up --build
```

API: http://localhost:8080
Inbox: http://localhost:8080/inbox

## Quick Start Flow

1) Create a tenant
```bash
curl -X POST http://localhost:8080/api/tenants \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Tenant"}'
```

2) Create a flow
```bash
curl -X POST http://localhost:8080/api/flows \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": 1,
    "name": "Welcome Flow",
    "definition": {
      "nodes": [
        {"id":"start","type":"send_message","message":"Hi! What can I help with today?","next":"q1"},
        {"id":"q1","type":"ask_question","prompt":"Please describe your request.","next":"end"},
        {"id":"end","type":"end"}
      ]
    }
  }'
```

3) Simulate an inbound message
```bash
curl -X POST http://localhost:8080/api/dev/simulate \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":1,"from_number":"+15555550123","text":"Hello"}'
```

Then open the inbox to see conversation + messages.

## Render Deploy

- Commit and push the repo.
- Create a new Render Blueprint using `render.yaml`.
- Set `DATABASE_URL` and `REDIS_URL` are auto-wired from managed services.

## Notes

- This MVP uses a deterministic flow engine and does not send WhatsApp messages. It stores outbound messages in the DB.
- The WhatsApp webhook is ready to receive inbound events once you have WABA credentials.
