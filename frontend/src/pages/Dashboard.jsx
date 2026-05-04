import { useEffect, useState, useCallback } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import {
  IconRefresh,
  IconCopy,
  IconAlertTriangle,
  IconBolt,
  IconDatabase,
  IconBroadcast,
  IconChartPie,
  IconHash,
  IconTags,
  IconClipboardList,
  IconFileText,
  IconShieldCheck,
} from '@tabler/icons-react';
import { briefs, intel } from '../api/client';
import Layout from '../components/Layout';
import SeverityBadge from '../components/SeverityBadge';

const SEV_COLORS = {
  CRITICAL: '#fb7185',
  HIGH: '#fb923c',
  MEDIUM: '#fbbf24',
  LOW: '#38bdf8',
  UNKNOWN: '#64748b',
};

function Stat({ label, value, hint, accent, Icon }) {
  return (
    <div className="glass rounded-xl p-5 relative overflow-hidden">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-400">
        {Icon && <Icon size={14} stroke={1.75} />}
        {label}
      </div>
      <div className={`mt-1 text-3xl font-semibold tabular-nums ${accent || 'text-white'}`}>
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

function Section({ title, Icon, action, children }) {
  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-300 flex items-center gap-2">
          {Icon && <Icon size={14} stroke={1.75} className="text-slate-400" />}
          {title}
        </h2>
        {action}
      </div>
      {children}
    </div>
  );
}

function ProgressDot({ status }) {
  const map = {
    pending: 'bg-slate-500',
    running: 'bg-sky-400 animate-pulse',
    succeeded: 'bg-emerald-400',
    failed: 'bg-rose-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${map[status] || 'bg-slate-500'}`} />;
}

function Dashboard() {
  const [brief, setBrief] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [b, s] = await Promise.allSettled([briefs.getLatest(), intel.getStats()]);
    if (b.status === 'fulfilled') setBrief(b.value.data);
    else setBrief(null);
    if (s.status === 'fulfilled') setStats(s.value.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const triggerScrape = async () => {
    try {
      const res = await intel.triggerScrape();
      const id = res.data.id;
      setScraping({ id, status: 'pending' });
      const poll = setInterval(async () => {
        try {
          const j = await intel.getJob(id);
          setScraping(j.data);
          if (j.data.status === 'succeeded' || j.data.status === 'failed') {
            clearInterval(poll);
            await load();
            setTimeout(() => setScraping(null), 3000);
          }
        } catch (e) {
          clearInterval(poll);
        }
      }, 2000);
    } catch (e) {
      const msg =
        e.response?.data?.message ||
        e.response?.data?.error ||
        e.response?.data?.detail ||
        'Scrape failed to start.';
      alert(msg);
    }
  };

  const copyAsMarkdown = () => {
    if (!brief) return;
    let md = `# Threat Intelligence Brief — ${new Date(brief.date).toLocaleDateString()}\n\n`;
    md += `## Executive Summary\n${brief.summary_md}\n\n## Top CVEs\n`;
    (brief.top_cves || []).forEach((c) => {
      md += `- **${c.cve_id}** (CVSS ${c.cvss_score}) — ${c.exploitation_status} — ${c.impact_summary}\n`;
    });
    md += `\n## Threat Themes\n`;
    (brief.threat_themes || []).forEach((t) => (md += `- ${t}\n`));
    md += `\n## Recommendations\n${brief.recommendations_md || ''}\n`;
    navigator.clipboard.writeText(md);
  };

  const sevData = stats
    ? Object.entries(stats.severity).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <Layout>
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
        <div>
          <div className="text-xs uppercase tracking-widest text-slate-400">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Daily Intelligence Brief</h1>
          <div className="text-slate-400 text-sm mt-1">
            Aggregated from open-source security feeds in the last 24 hours.
          </div>
        </div>
        <div className="flex items-center gap-2">
          {scraping && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-slate-800/60 text-xs">
              <ProgressDot status={scraping.status} />
              <span className="text-slate-300">
                Scrape {scraping.status}
                {scraping.items_stored ? ` · ${scraping.items_stored} new` : ''}
              </span>
            </div>
          )}
          <button
            onClick={triggerScrape}
            className="px-3.5 py-2 rounded-md bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium shadow-lg shadow-purple-900/30 inline-flex items-center gap-1.5"
          >
            <IconRefresh size={16} stroke={1.75} />
            Refresh feeds
          </button>
          <button
            onClick={copyAsMarkdown}
            className="px-3.5 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-medium inline-flex items-center gap-1.5"
          >
            <IconCopy size={16} stroke={1.75} />
            Copy as Markdown
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Stat
          label="Items collected"
          value={stats?.total_items ?? '—'}
          hint={`${stats?.items_last_24h ?? 0} in last 24h`}
          Icon={IconDatabase}
        />
        <Stat
          label="Critical"
          value={stats?.severity?.CRITICAL ?? 0}
          accent="text-rose-300"
          Icon={IconAlertTriangle}
        />
        <Stat
          label="High"
          value={stats?.severity?.HIGH ?? 0}
          accent="text-orange-300"
          Icon={IconBolt}
        />
        <Stat
          label="Sources active"
          value={stats?.sources?.length ?? 0}
          hint={(stats?.sources || []).map((s) => s.source).slice(0, 4).join(' · ')}
          Icon={IconBroadcast}
        />
      </div>

      {loading && <div className="text-slate-400">Loading…</div>}

      {!loading && !brief && (
        <Section title="No brief yet" Icon={IconClipboardList}>
          <div className="text-slate-400 text-sm">
            Click <em>Refresh feeds</em> above to scrape the latest intel and generate today&apos;s
            brief.
          </div>
        </Section>
      )}

      {!loading && brief && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Section title="Executive summary" Icon={IconFileText}>
              <p className="text-slate-200 leading-relaxed">{brief.summary_md}</p>
              {(brief.high_priority_flags || []).length > 0 && (
                <div className="mt-4 p-3 rounded-lg bg-rose-500/10 ring-1 ring-rose-500/30">
                  <div className="text-xs uppercase tracking-widest text-rose-300 mb-2">
                    High-priority flags
                  </div>
                  <ul className="text-rose-100 text-sm space-y-1 list-disc pl-5">
                    {brief.high_priority_flags.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Section>

            <Section title="Top CVEs" Icon={IconAlertTriangle}>
              <div className="overflow-x-auto -mx-2">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-left">
                      <th className="px-2 py-2 font-medium">CVE</th>
                      <th className="px-2 py-2 font-medium">CVSS</th>
                      <th className="px-2 py-2 font-medium">Exploitation</th>
                      <th className="px-2 py-2 font-medium">Affected</th>
                      <th className="px-2 py-2 font-medium">Impact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(brief.top_cves || []).map((c, i) => (
                      <tr
                        key={i}
                        className="border-t border-slate-800/60 hover:bg-slate-800/30"
                      >
                        <td className="px-2 py-2 mono text-purple-300 font-medium">
                          {c.cve_id}
                        </td>
                        <td className="px-2 py-2">
                          <SeverityBadge score={c.cvss_score} />
                        </td>
                        <td className="px-2 py-2 text-slate-300">
                          {c.exploitation_status?.replace(/_/g, ' ') || '—'}
                        </td>
                        <td className="px-2 py-2 text-slate-300">{c.affected_products}</td>
                        <td className="px-2 py-2 text-slate-400">
                          {c.impact_summary?.slice(0, 140) || '—'}
                        </td>
                      </tr>
                    ))}
                    {!brief.top_cves?.length && (
                      <tr>
                        <td colSpan="5" className="px-2 py-6 text-center text-slate-500">
                          No CVEs in today&apos;s feed.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Section>

            <Section title="Defensive recommendations" Icon={IconShieldCheck}>
              <ol className="space-y-2 text-slate-200 text-sm list-decimal pl-5">
                {(brief.recommendations_md || '').split('\n').filter(Boolean).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ol>
            </Section>
          </div>

          <div className="space-y-6">
            <Section title="Severity mix" Icon={IconChartPie}>
              <div className="h-44">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      dataKey="value"
                      data={sevData}
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={2}
                    >
                      {sevData.map((d) => (
                        <Cell key={d.name} fill={SEV_COLORS[d.name] || '#64748b'} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: 8,
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                {sevData.map((d) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: SEV_COLORS[d.name] || '#64748b' }}
                    />
                    <span className="text-slate-300">{d.name}</span>
                    <span className="ml-auto mono text-slate-400">{d.value}</span>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Threat themes" Icon={IconTags}>
              <div className="flex flex-wrap gap-2">
                {(brief.threat_themes || []).map((t, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-200 text-xs ring-1 ring-slate-700"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </Section>

            <Section title="Sources" Icon={IconBroadcast}>
              <div className="h-40">
                <ResponsiveContainer>
                  <BarChart data={stats?.sources || []}>
                    <XAxis
                      dataKey="source"
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      axisLine={{ stroke: '#1e293b' }}
                    />
                    <YAxis
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      axisLine={{ stroke: '#1e293b' }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#0f172a',
                        border: '1px solid #1e293b',
                        borderRadius: 8,
                      }}
                    />
                    <Bar dataKey="count" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Section>

            {!!stats?.top_techniques?.length && (
              <Section title="MITRE ATT&CK signal" Icon={IconHash}>
                <div className="flex flex-wrap gap-2">
                  {stats.top_techniques.map((t) => (
                    <span
                      key={t.technique}
                      className="px-2 py-1 rounded mono text-[11px] bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/30"
                      title={`${t.count} item(s)`}
                    >
                      {t.technique} · {t.count}
                    </span>
                  ))}
                </div>
              </Section>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}

export default Dashboard;
