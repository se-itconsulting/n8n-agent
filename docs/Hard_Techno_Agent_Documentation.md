# Hard Techno Agent Documentation

This document explains how to run the n8n Agent with a Python microservice and a Postgres database, plus example flows for a Hard Techno use case.

## Components

- n8n: automation platform (Docker)
- Python Service (FastAPI): endpoints for tracks, Beatport Top 100 (mock), and ratings
- Postgres: data persistence
- Optional: Traefik for HTTPS and domain routing

## Endpoints (Python Service)

- GET /healthz
- GET /beatport/top100?genre=hard-techno&limit=10
- POST /tracks { title, artist, bpm?, source? }
- GET /tracks?limit=50
- POST /ratings { track_id, rating (1..5), user_name?, comment? }

## Database Schema

- gen_tracks(id, title, artist, bpm, source, created_at)
- stems(id, track_id, type, url, created_at)
- ratings(id, track_id, rating, user_name, comment, created_at)

See `sql/schema.sql`.

## n8n Flows

- flows/hello-world.json: Cron → Function
- flows/pyapi-beatport.json: Cron → GET /beatport/top100 → map → POST /tracks
- flows/rating-webhook.json: Webhook → normalize → POST /ratings

## Run (development)

1. docker compose up -d
2. Open n8n at http://localhost:5678
3. Import flows from `flows/` via n8n UI
4. Run SQL init once inside DB container or via admin tool: `psql -U n8n -d n8n -f /sql/schema.sql` (mount or copy first)

For HTTPS and domain, use docker-compose-traefik.yml and set env vars: N8N_HOST, N8N_ENCRYPTION_KEY, ACME_EMAIL, PYAPI_HOST.

## Notes

- Beatport Top 100 is a stub. Replace with a real integration or API.
- Adjust timezone, ports, and resource limits as needed.
- Back up volumes `n8n_data` and `db_data`.
