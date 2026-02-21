export type LeaderRow = {
  login: string;
  impact_score: number;
  authored_score: number;
  collaboration_score: number;
  merged_prs: number;
  avg_merge_days: number | null;
  lines_changed: number;
  updated_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080";

export async function fetchLeaderboard(
  days = 5,
): Promise<{ days: number; top5: LeaderRow[] }> {
  const res = await fetch(`${API_BASE}/api/leaderboard?days=${days}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json();
}

export async function fetchEngineer(login: string, days = 5) {
  const res = await fetch(
    `${API_BASE}/api/engineer/${encodeURIComponent(login)}?days=${days}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Backend error: ${res.status}`);
  return res.json();
}
