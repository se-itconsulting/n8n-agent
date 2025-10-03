# n8n-agent

Containerized n8n + Python service starter for a Hard Techno agent. Includes example flows and a Postgres DB.

## What's inside

- docker-compose.yml: base stack (n8n, Postgres, FastAPI service)
- docker-compose-traefik.yml: optional Traefik with HTTPS
- python-svc: FastAPI microservice
- flows: ready-to-import n8n flows
- sql/schema.sql: database tables
- docs/Hard_Techno_Agent_Documentation.md: overview

## Quickstart

1. Start services

```pwsh
cd d:\Development\n8n\n8n-agent
$env:COMPOSE_PROJECT_NAME="n8n-agent"
docker compose up -d --build
```

2. Initialize DB schema

Option A: Exec into DB and run schema

```pwsh
docker exec -it n8n-agent-db bash -lc "psql -U n8n -d n8n -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto;'"
docker cp .\sql\schema.sql n8n-agent-db:/schema.sql
docker exec -it n8n-agent-db bash -lc "psql -U n8n -d n8n -f /schema.sql"
```

3. Open n8n UI

- <http://localhost:5678>

4. Import flows

- In n8n, import JSON from `flows/` for each flow

5. Test Python service

- <http://localhost:8000/healthz>
- <http://localhost:8000/beatport/top100?genre=hard-techno&limit=5>

## Traefik (optional)

Set environment variables and use the Traefik compose file:

```pwsh
$env:N8N_HOST="n8n.example.com"
$env:PYAPI_HOST="pyapi.example.com"
$env:ACME_EMAIL="you@example.com"
$env:N8N_ENCRYPTION_KEY=[guid]  # 32+ chars recommended

docker compose -f docker-compose-traefik.yml up -d
```

## Configuration

- DATABASE_URL for python-svc: set in compose (postgresql+psycopg2://n8n:n8n@db:5432/n8n)
- Timezone: GENERIC_TIMEZONE in n8n

## Notes

- Beatport endpoint is a stub. Replace with a real API integration.
- Volumes: `n8n_data`, `db_data` persist data.
