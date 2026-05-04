import { Link, NavLink } from 'react-router-dom';
import {
  IconShieldHalfFilled,
  IconLayoutDashboard,
  IconRadar2,
  IconArchive,
  IconSettings,
} from '@tabler/icons-react';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', Icon: IconLayoutDashboard },
  { to: '/intel', label: 'Raw Feed', Icon: IconRadar2 },
  { to: '/briefs', label: 'Archive', Icon: IconArchive },
  { to: '/settings', label: 'Settings', Icon: IconSettings },
];

function Layout({ children }) {
  return (
    <div className="min-h-screen text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-800/60 bg-slate-950/70 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <span className="grid place-items-center w-9 h-9 rounded-lg bg-gradient-to-br from-purple-500 to-violet-700 ring-1 ring-purple-400/30 shadow-lg shadow-purple-900/40 group-hover:scale-105 transition">
              <IconShieldHalfFilled size={20} stroke={2} className="text-white" />
            </span>
            <div className="leading-tight">
              <div className="font-semibold text-[15px] tracking-tight">Threat Intel</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">
                Summarizer
              </div>
            </div>
          </Link>
          <nav className="flex gap-1">
            {NAV.map(({ to, label, Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium transition flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-purple-600/20 text-purple-200 ring-1 ring-purple-500/40'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon size={16} stroke={1.75} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>

      <footer className="max-w-7xl mx-auto px-6 py-6 text-xs text-slate-500">
        Threat Intelligence Summarizer · open-source feeds → daily briefs
      </footer>
    </div>
  );
}

export default Layout;
