import os
from datetime import datetime, timezone, timedelta
from math import log10
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Always load .env from this folder
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OWNER = os.getenv("GITHUB_OWNER", "")
REPO = os.getenv("GITHUB_REPO", "")
SYNC_TOKEN = os.getenv("SYNC_TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_SCHEMA = os.getenv("SUPABASE_SCHEMA", "public")

# This controls how much GitHub history sync pulls for testing
# Set DAYS_TO_SYNC=5 in .env for quick test
DAYS_TO_SYNC = int(os.getenv("DAYS_TO_SYNC", "90"))

if not all([GITHUB_TOKEN, OWNER, REPO, SYNC_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
    raise RuntimeError("Missing env vars. Check backend/.env")

app = FastAPI(title="Impact Backend (Supabase HTTP)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def gh_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "impact-dashboard",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def repo_base() -> str:
    return f"https://api.github.com/repos/{OWNER}/{REPO}"


def sb_base() -> str:
    return f"{SUPABASE_URL}/rest/v1"


def sb_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


async def sb_get(table: str, params: Dict[str, str]) -> Any:
    url = f"{sb_base()}/{table}?{urlencode(params)}"
    async with httpx.AsyncClient(timeout=60, headers=sb_headers()) as client:
        r = await client.get(url, headers={"Accept-Profile": SUPABASE_SCHEMA})
        if r.status_code >= 400:
            raise HTTPException(
                500, f"Supabase GET failed: {r.status_code} {r.text}")
        return r.json()


async def sb_upsert(table: str, rows: List[Dict[str, Any]], on_conflict: str = "id") -> None:
    if not rows:
        return
    url = f"{sb_base()}/{table}?on_conflict={on_conflict}"
    async with httpx.AsyncClient(timeout=60, headers=sb_headers()) as client:
        r = await client.post(url, headers={"Content-Profile": SUPABASE_SCHEMA}, json=rows)
        if r.status_code >= 400:
            raise HTTPException(
                500, f"Supabase UPSERT failed: {r.status_code} {r.text}")


async def sb_patch(table: str, match: str, patch_obj: Dict[str, Any]) -> None:
    url = f"{sb_base()}/{table}?{match}"
    async with httpx.AsyncClient(timeout=60, headers=sb_headers()) as client:
        r = await client.patch(url, headers={"Content-Profile": SUPABASE_SCHEMA}, json=patch_obj)
        if r.status_code >= 400:
            raise HTTPException(
                500, f"Supabase PATCH failed: {r.status_code} {r.text}")


async def gh_get(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    async with httpx.AsyncClient(timeout=60, headers=gh_headers()) as client:
        r = await client.get(url, params=params)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return r.json()


async def get_cursor() -> Optional[datetime]:
    rows = await sb_get("sync_state", {"select": "cursor_updated_at", "id": "eq.default", "limit": "1"})
    if not rows:
        return None
    v = rows[0].get("cursor_updated_at")
    return to_dt(v) if v else None


async def set_cursor(dt: datetime) -> None:
    await sb_patch("sync_state", "id=eq.default", {"cursor_updated_at": dt.isoformat()})


def pr_points(merged: bool, lines_changed: int, changed_files: int, merge_days: Optional[float]) -> float:
    shipped = 8.0 if merged else 0.0
    complexity = min(3.0, log10(1.0 + max(lines_changed, 0))) + \
        min(2.0, max(changed_files, 0) / 10.0)
    speed_bonus = 0.0
    if merged and merge_days is not None:
        speed_bonus = max(0.0, 2.0 - min(2.0, merge_days / 7.0))
    churn_penalty = 1.5 if lines_changed >= 2500 else 0.0
    return shipped + complexity + speed_bonus - churn_penalty


@app.get("/api/health")
def health():
    return {"ok": True, "time": utc_now().isoformat().replace("+00:00", "Z")}


@app.post("/api/sync")
async def sync(x_sync_token: str = Header(default="")):
    if x_sync_token != SYNC_TOKEN:
        raise HTTPException(401, "Invalid sync token")

    cursor = await get_cursor()

    # Only sync PRs updated within the last DAYS_TO_SYNC days
    cutoff = utc_now() - timedelta(days=DAYS_TO_SYNC)

    newest = cursor
    processed = 0

    for page in range(1, 21):
        prs = await gh_get(
            f"{repo_base()}/pulls",
            {"state": "all", "sort": "updated",
                "direction": "desc", "per_page": 100, "page": page},
        )
        if not prs:
            break

        stop = False
        pr_rows: List[Dict[str, Any]] = []
        review_rows: List[Dict[str, Any]] = []

        for pr in prs:
            upd = to_dt(pr["updated_at"])

            # Stop fetching older history for testing
            if upd < cutoff:
                stop = True
                break

            # Incremental sync stop condition
            if cursor and upd < cursor:
                stop = True
                break

            d = await gh_get(f"{repo_base()}/pulls/{int(pr['number'])}")
            pr_rows.append({
                "id": pr["id"],
                "number": pr["number"],
                "author": pr["user"]["login"] if pr.get("user") else None,
                "title": pr.get("title"),
                "state": pr.get("state"),
                "merged": bool(d.get("merged")),
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "merged_at": d.get("merged_at"),
                "additions": int(d.get("additions") or 0),
                "deletions": int(d.get("deletions") or 0),
                "changed_files": int(d.get("changed_files") or 0),
            })

            rvs = await gh_get(f"{repo_base()}/pulls/{int(pr['number'])}/reviews", {"per_page": 100})
            for rv in rvs:
                review_rows.append({
                    "id": rv["id"],
                    "pr_id": pr["id"],
                    "reviewer": rv["user"]["login"] if rv.get("user") else None,
                    "state": rv.get("state"),
                    "submitted_at": rv.get("submitted_at"),
                })

            newest = upd if (newest is None or upd > newest) else newest
            processed += 1

        await sb_upsert("prs", pr_rows, on_conflict="id")
        await sb_upsert("reviews", review_rows, on_conflict="id")

        if stop:
            break

    if newest:
        await set_cursor(newest)

    return {
        "processed_prs": processed,
        "days_to_sync": DAYS_TO_SYNC,
        "cursor_before": cursor.isoformat() if cursor else None,
        "cursor_after": newest.isoformat() if newest else None,
    }


@app.get("/api/leaderboard")
async def leaderboard(days: int = 90):
    start = (utc_now() - timedelta(days=days)).isoformat()

    prs = await sb_get(
        "prs",
        {
            "select": "author,created_at,merged_at,merged,additions,deletions,changed_files,updated_at,title,number,state",
            "updated_at": f"gte.{start}",
            "limit": "5000",
        },
    )
    reviews = await sb_get(
        "reviews",
        {
            "select": "reviewer,state,submitted_at",
            "submitted_at": f"gte.{start}",
            "limit": "5000",
        },
    )

    authored: Dict[str, Dict[str, float]] = {}
    for p in prs:
        login = p.get("author")
        if not login:
            continue

        created_at = to_dt(p["created_at"])
        merged_at = to_dt(p["merged_at"]) if p.get("merged_at") else None
        merged = bool(p.get("merged"))
        lines_changed = int((p.get("additions") or 0) +
                            (p.get("deletions") or 0))
        changed_files = int(p.get("changed_files") or 0)

        merge_days = None
        if merged and merged_at:
            merge_days = (merged_at - created_at).total_seconds() / 86400.0

        pts = pr_points(merged, lines_changed, changed_files, merge_days)
        authored.setdefault(login, {"authored": 0.0, "merged_prs": 0.0})
        authored[login]["authored"] += pts
        authored[login]["merged_prs"] += 1.0 if merged else 0.0

    collab: Dict[str, float] = {}
    for r in reviews:
        reviewer = r.get("reviewer")
        if not reviewer:
            continue
        st = (r.get("state") or "").upper()
        collab[reviewer] = collab.get(reviewer, 0.0) + (
            2.0 if st == "APPROVED" else 1.0 if st == "CHANGES_REQUESTED" else 0.5
        )

    people = set(authored.keys()) | set(collab.keys())
    out = []
    for login in people:
        a = authored.get(login, {"authored": 0.0, "merged_prs": 0.0})
        c = collab.get(login, 0.0)
        out.append({
            "login": login,
            "impact_score": round(float(a["authored"] + c), 3),
            "authored_score": round(float(a["authored"]), 3),
            "collaboration_score": round(float(c), 3),
            "merged_prs": int(a["merged_prs"]),
        })

    out.sort(key=lambda x: x["impact_score"], reverse=True)
    return {"days": days, "top5": out[:5]}
