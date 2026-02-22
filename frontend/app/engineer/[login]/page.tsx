import Link from "next/link";
import { fetchEngineer } from "../../../lib/api";
import { fmt } from "../../../lib/format";

export default async function EngineerPage({
  params,
}: {
  params: { login: string };
}) {
  const login = params.login;

  let data: any;
  try {
    data = await fetchEngineer(login, 5);
  } catch (e: any) {
    return (
      <div className="card">
        <div className="h1">{login}</div>
        <div className="muted">Could not load engineer details.</div>
        <div className="sep" />
        <Link className="btn" href="/">
          Back
        </Link>
      </div>
    );
  }

  return (
    <div className="grid">
      <div className="card">
        <div className="row">
          <div>
            <div className="h1">{data.login}</div>
            <div className="muted">Window: last {data.days} days</div>
          </div>
          <Link className="btn" href="/">
            Back
          </Link>
        </div>

        <div className="sep" />
        <div className="grid grid2">
          <div className="card">
            <div className="muted">Impact score</div>
            <div className="kpi">{fmt(data.impact_score, 2)}</div>
          </div>
          <div className="card">
            <div className="muted">Merged PRs</div>
            <div className="kpi">{data.merged_prs}</div>
          </div>
          <div className="card">
            <div className="muted">Authored score</div>
            <div className="kpi">{fmt(data.authored_score, 2)}</div>
          </div>
          <div className="card">
            <div className="muted">Collaboration score</div>
            <div className="kpi">{fmt(data.collaboration_score, 2)}</div>
          </div>
        </div>

        <div className="sep" />
      </div>

      <div className="card">
        <div className="h2">Recent authored PRs (sample)</div>
        <div className="muted">
          This is a small sample of authored PRs from the window.
        </div>
        <div className="sep" />
        <div className="grid">
          {(data.sample_prs || []).map((p: any) => (
            <div key={p.number} className="card">
              <div className="row">
                <div className="h2">#{p.number}</div>
                <span className="badge">{p.merged ? "merged" : p.state}</span>
              </div>
              <div className="muted">{p.title}</div>
              <div className="sep" />
              <div className="muted">
                points {fmt(p.pr_points, 2)} · lines {p.lines_changed} · files{" "}
                {p.changed_files} · merge days{" "}
                {p.merge_days === null ? "-" : fmt(p.merge_days, 2)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
