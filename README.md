# Engineer Impact Dashboard (Frontend + Backend)

## Quick start
### Backend
1) Create tables: run backend/schema.sql in your Postgres
2) cd backend
3) cp .env.example .env and set values
4) pip install -r requirements.txt
5) uvicorn main:app --reload --port 8080
6) Trigger sync:
   curl -X POST http://localhost:8080/api/sync -H "x-sync-token: <SYNC_TOKEN>"

### Frontend
1) cd frontend
2) cp .env.example .env.local and set NEXT_PUBLIC_API_BASE
3) npm install
4) npm run dev

## Notes
- Frontend reads only from backend for fast public loads.
- Backend stores PRs and reviews in Postgres and computes impact on request.
