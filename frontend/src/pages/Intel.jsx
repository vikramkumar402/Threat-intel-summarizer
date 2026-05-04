import { useEffect, useMemo, useState } from 'react';
import { IconSearch, IconExternalLink, IconFilter } from '@tabler/icons-react';
import { intel } from '../api/client';
import Layout from '../components/Layout';
import SeverityBadge from '../components/SeverityBadge';

const SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'];

function IocChip({ ioc }) {
  const palette = {
    cve: 'bg-purple-500/10 text-purple-300 ring-purple-500/30',
    ipv4: 'bg-rose-500/10 text-rose-300 ring-rose-500/30',
    domain: 'bg-sky-500/10 text-sky-300 ring-sky-500/30',
    url: 'bg-cyan-500/10 text-cyan-300 ring-cyan-500/30',
    sha256: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/30',
    sha1: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/30',
    md5: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/30',
    email: 'bg-amber-500/10 text-amber-300 ring-amber-500/30',
  };
  return (
    <span
      className={`mono text-[10px] px-1.5 py-0.5 rounded ring-1 ${
        palette[ioc.type] || 'bg-slate-500/10 text-slate-300 ring-slate-500/30'
      }`}
      title={ioc.type}
    >
      {ioc.value.length > 38 ? `${ioc.value.slice(0, 38)}…` : ioc.value}
    </span>
  );
}

function Intel() {
  const [items, setItems] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ severity: '', source: '', q: '' });

  useEffect(() => {
    intel.listSources().then((r) => setSources(r.data.sources || [])).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = { page: 1, limit: 100 };
    if (filters.severity) params.severity = filters.severity;
    if (filters.source) params.source = filters.source;
    if (filters.q) params.q = filters.q;
    intel
      .getItems(params)
      .then((r) => setItems(r.data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [filters]);

  const counts = useMemo(() => {
    const c = Object.fromEntries(SEVERITIES.map((s) => [s, 0]));
    items.forEach((i) => {
      const s = (i.severity || 'UNKNOWN').toUpperCase();
      if (s in c) c[s] += 1;
    });
    return c;
  }, [items]);

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Raw Intelligence Feed</h1>
          <p className="text-sm text-slate-400 mt-1">
            {items.length} items shown · CRITICAL {counts.CRITICAL} · HIGH {counts.HIGH}
          </p>
        </div>
      </div>

      <div className="glass rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[220px]">
          <IconSearch
            size={16}
            stroke={1.75}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
          />
          <input
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            placeholder="Search title, description, IOCs…"
            className="w-full bg-slate-900/70 border border-slate-700 rounded-md pl-9 pr-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>
        <select
          value={filters.severity}
          onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
          className="bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={filters.source}
          onChange={(e) => setFilters({ ...filters, source: e.target.value })}
          className="bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100"
        >
          <option value="">All sources</option>
          {sources.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-slate-400">Loading…</div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <article
              key={item.id}
              className="glass rounded-xl p-4 hover:ring-1 hover:ring-purple-500/30 transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 text-xs">
                    <SeverityBadge severity={item.severity} />
                    <span className="text-purple-300 font-semibold">{item.source}</span>
                    {item.published_at && (
                      <span className="text-slate-500">
                        {new Date(item.published_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  <h3 className="text-slate-100 font-semibold leading-snug">{item.title}</h3>
                  <p className="text-slate-400 text-sm mt-1 line-clamp-2">{item.raw_text}</p>

                  {(item.iocs?.length > 0 || item.mitre_techniques?.length > 0) && (
                    <div className="mt-3 flex flex-wrap items-center gap-1.5">
                      {(item.mitre_techniques || []).map((t) => (
                        <span
                          key={t}
                          className="mono text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/30"
                        >
                          {t}
                        </span>
                      ))}
                      {(item.iocs || []).slice(0, 8).map((ioc, i) => (
                        <IocChip key={i} ioc={ioc} />
                      ))}
                      {item.iocs?.length > 8 && (
                        <span className="text-[10px] text-slate-500">+{item.iocs.length - 8} more</span>
                      )}
                    </div>
                  )}
                </div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-purple-300 hover:text-purple-200 whitespace-nowrap inline-flex items-center gap-1"
                >
                  Source <IconExternalLink size={12} stroke={2} />
                </a>
              </div>
            </article>
          ))}
          {!items.length && (
            <div className="glass rounded-xl p-8 text-center text-slate-400">
              No items match these filters.
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}

export default Intel;
