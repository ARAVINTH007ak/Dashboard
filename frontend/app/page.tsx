import Link from "next/link";
import { fetchLeaderboard } from "../lib/api";
import { fmt } from "../lib/format";

export default async function Page() {
  let data;

  try {
    data = await fetchLeaderboard(5);
  } catch (e: any) {
    return (
      <div className="grid">
        <div className="card">
          <div className="h1">Engineer Impact Dashboard</div>
          <div className="muted">Could not load data from backend.</div>
          <div className="sep" />
          <div className="muted">{String(e?.message || e)}</div>
          <div className="sep" />
          <div className="muted">
            Set NEXT_PUBLIC_API_BASE in frontend/.env.local
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid">
      {/* Header */}
      <div className="card">
        <div className="h1">Engineer Impact Dashboard</div>
        <div className="muted">
          Measures shipped outcomes plus enabling others. Window: last 90 days.
        </div>
      </div>

      {/* Leaderboard Cards */}
      <div className="grid2">
        {data.top5.map((r, i) => (
          <Link
            key={r.login}
            href={`/engineer/${r.login}`}
            className={`card ${i < 3 ? "top-card" : ""}`}
          >
            {/* Top Section */}
            <div className="row space">
              <div className="row gap">
                <div className={`rank rank-${i + 1}`}>
                  #{i + 1}
                </div>

                <div>
                  <div className="h2">{r.login}</div>
                  <span className="badge">
                    impact {fmt(r.impact_score, 2)}
                  </span>
                </div>
              </div>

              <div className="muted small">
                merged PRs {r.merged_prs}
              </div>
            </div>

            <div className="sep" />

            {/* Scores */}
            <div className="grid">
              <div className="row space">
                <span className="muted">Authored</span>
                <span className="kpi">
                  {fmt(r.authored_score, 2)}
                </span>
              </div>

              <div className="row space">
                <span className="muted">Collaboration</span>
                <span className="kpi">
                  {fmt(r.collaboration_score, 2)}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Footer */}
      <div className="card">
        <div className="h2">How impact is scored</div>
        <div className="muted">
          We score impact per PR using shipped outcomes, complexity
          (log-scaled change size + files changed), speed-to-merge bonus,
          and a small churn penalty for unusually large PRs. We add
          collaboration points from reviewing others&apos; PRs.
        </div>
      </div>
    </div>
  );
}