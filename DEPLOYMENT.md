# Render Deployment

This repo is ready to deploy with a Render Blueprint.

## Files Render Uses

- `render.yaml`
- `apps/api/Dockerfile`
- `apps/worker/Dockerfile`

## Steps

1. Push this repo to GitHub.
2. In Render, click "New" → "Blueprint".
3. Select your repo and approve the `render.yaml` plan.
4. Render will provision:
   - `waba-db` (Postgres)
   - `waba-redis` (Redis)
   - `waba-api` (web service)
   - `waba-worker` (worker)
5. After deploy, open:
   - API: `https://<your-api-service>.onrender.com/health`
   - Inbox UI: `https://<your-api-service>.onrender.com/inbox`

## Environment Variables

Render wires these automatically from the managed services:

- `DATABASE_URL`
- `REDIS_URL`

## Webhook

When you have WhatsApp Business Platform credentials, set the webhook URL to:

`https://<your-api-service>.onrender.com/webhook/whatsapp`

## Test (no WABA credentials)

Use the simulate endpoint:

`POST /api/dev/simulate`

Example payload:
```json
{ "tenant_id": 1, "from_number": "+15555550123", "text": "Hello" }
```
