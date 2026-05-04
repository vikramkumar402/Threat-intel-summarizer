import { useEffect, useState } from 'react';
import { auth, intel, users } from '../api/client';
import Layout from '../components/Layout';

const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

function Settings() {
  const [user, setUser] = useState(null);
  const [sources, setSources] = useState([]);
  const [form, setForm] = useState({
    receive_digest: true,
    digest_time: '06:00',
    timezone: 'UTC',
    severity_threshold: 'LOW',
    subscribed_sources: [],
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    auth
      .getMe()
      .then((r) => {
        setUser(r.data);
        setForm((f) => ({
          ...f,
          receive_digest: r.data.receive_digest,
          severity_threshold: r.data.severity_threshold || 'LOW',
          subscribed_sources: r.data.subscribed_sources || [],
        }));
      })
      .catch(() => setUser({ email: 'anonymous@local', role: 'viewer' }));
    intel.listSources().then((r) => setSources(r.data.sources || [])).catch(() => {});
  }, []);

  const toggleSource = (s) => {
    setForm((f) => ({
      ...f,
      subscribed_sources: f.subscribed_sources.includes(s)
        ? f.subscribed_sources.filter((x) => x !== s)
        : [...f.subscribed_sources, s],
    }));
  };

  const save = async () => {
    try {
      await users.updateDigestSettings(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      alert(e.response?.data?.message || 'Failed to save');
    }
  };

  return (
    <Layout>
      <h1 className="text-3xl font-bold tracking-tight mb-6">Settings</h1>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="glass rounded-xl p-6">
          <h2 className="text-xs uppercase tracking-widest text-slate-400 mb-3">Account</h2>
          <div className="space-y-1 text-sm">
            <div className="text-slate-400">Email</div>
            <div className="text-slate-100">{user?.email || '—'}</div>
            <div className="mt-3 text-slate-400">Role</div>
            <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[11px] uppercase tracking-wide bg-purple-500/15 text-purple-200 ring-1 ring-purple-500/30">
              {user?.role || 'viewer'}
            </span>
          </div>
        </div>

        <div className="glass rounded-xl p-6 lg:col-span-2 space-y-5">
          <h2 className="text-xs uppercase tracking-widest text-slate-400">Email digest</h2>

          <label className="flex items-center gap-3 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={form.receive_digest}
              onChange={(e) => setForm({ ...form, receive_digest: e.target.checked })}
              className="w-4 h-4 accent-purple-500"
            />
            Receive daily email digest
          </label>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Delivery time</label>
              <input
                type="time"
                value={form.digest_time}
                onChange={(e) => setForm({ ...form, digest_time: e.target.value })}
                className="w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Timezone</label>
              <select
                value={form.timezone}
                onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                className="w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100"
              >
                {['UTC', 'Asia/Kolkata', 'America/New_York', 'Europe/London'].map((tz) => (
                  <option key={tz}>{tz}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Minimum severity</label>
            <div className="flex gap-2">
              {SEVERITIES.map((s) => (
                <button
                  key={s}
                  onClick={() => setForm({ ...form, severity_threshold: s })}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                    form.severity_threshold === s
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-400 mb-2">Subscribed sources</div>
            <div className="flex flex-wrap gap-2">
              {sources.map((s) => {
                const active = form.subscribed_sources.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() => toggleSource(s)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition ring-1 ${
                      active
                        ? 'bg-purple-600/25 text-purple-100 ring-purple-500/40'
                        : 'bg-slate-800 text-slate-300 ring-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={save}
              className="px-5 py-2 rounded-md bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold"
            >
              Save settings
            </button>
            {saved && <span className="text-emerald-400 text-sm">Saved ✓</span>}
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default Settings;
