# Backend (FastAPI + Postgres)

## 1) Create DB tables
Run `schema.sql` once in your Postgres (Supabase SQL editor is easiest).

## 2) Setup
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- cp .env.example .env
- fill values in .env

## 3) Run
- uvicorn main:app --host 0.0.0.0 --port 8080 --reload

## 4) Sync data
Trigger ingestion:
curl -X POST http://localhost:8080/api/sync -H "x-sync-token: change_me"

Then open:
- http://localhost:8080/api/leaderboard
