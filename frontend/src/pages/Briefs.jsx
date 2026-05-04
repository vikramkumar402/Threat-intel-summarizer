import { useEffect, useState } from 'react';
import { briefs } from '../api/client';
import Layout from '../components/Layout';

function Briefs() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(null);

  useEffect(() => {
    briefs
      .list({ page: 1, limit: 50 })
      .then((r) => {
        setList(r.data);
        if (r.data.length) setActive(r.data[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <h1 className="text-3xl font-bold tracking-tight mb-6">Brief Archive</h1>

      {loading ? (
        <div className="text-slate-400">Loading…</div>
      ) : !list.length ? (
        <div className="glass rounded-xl p-8 text-slate-400">No briefs generated yet.</div>
      ) : (
        <div className="grid lg:grid-cols-[280px,1fr] gap-6">
          <aside className="space-y-2">
            {list.map((b) => (
              <button
                key={b.id}
                onClick={() => setActive(b)}
                className={`w-full text-left glass rounded-lg p-3 hover:ring-1 hover:ring-purple-500/30 transition ${
                  active?.id === b.id ? 'ring-1 ring-purple-500/50' : ''
                }`}
              >
                <div className="text-sm font-semibold text-slate-100">
                  {new Date(b.date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {(b.top_cves || []).length} CVEs · {(b.threat_themes || []).length} themes
                </div>
              </button>
            ))}
          </aside>

          {active && (
            <div className="glass rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">
                  {new Date(active.date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </h2>
                <span className="text-xs text-slate-500">{active.item_count || 0} items analysed</span>
              </div>
              <p className="text-slate-200 leading-relaxed mb-6">{active.summary_md}</p>

              {!!active.top_cves?.length && (
                <>
                  <h3 className="text-xs uppercase tracking-widest text-slate-400 mb-2">
                    Top CVEs
                  </h3>
                  <ul className="space-y-1.5 mb-6">
                    {active.top_cves.map((c, i) => (
                      <li key={i} className="text-sm">
                        <span className="mono text-purple-300 font-semibold">{c.cve_id}</span>
                        <span className="text-slate-400"> — CVSS {c.cvss_score} — </span>
                        <span className="text-slate-300">{c.impact_summary?.slice(0, 200)}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {!!active.threat_themes?.length && (
                <>
                  <h3 className="text-xs uppercase tracking-widest text-slate-400 mb-2">
                    Themes
                  </h3>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {active.threat_themes.map((t, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-200 text-xs ring-1 ring-slate-700"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </>
              )}

              {active.recommendations_md && (
                <>
                  <h3 className="text-xs uppercase tracking-widest text-slate-400 mb-2">
                    Recommendations
                  </h3>
                  <ol className="space-y-1 text-sm text-slate-200 list-decimal pl-5">
                    {active.recommendations_md
                      .split('\n')
                      .filter(Boolean)
                      .map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                  </ol>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}

export default Briefs;
