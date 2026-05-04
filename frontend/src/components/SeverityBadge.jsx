function SeverityBadge({ severity, score }) {
  const tone = (() => {
    if (score !== undefined && score !== null) {
      if (score >= 9.0) return 'bg-rose-500/15 text-rose-300 ring-rose-500/30';
      if (score >= 7.0) return 'bg-orange-500/15 text-orange-300 ring-orange-500/30';
      if (score >= 4.0) return 'bg-amber-500/15 text-amber-300 ring-amber-500/30';
      if (score > 0) return 'bg-sky-500/15 text-sky-300 ring-sky-500/30';
    }
    switch ((severity || '').toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/15 text-rose-300 ring-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-300 ring-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-300 ring-amber-500/30';
      case 'LOW':
        return 'bg-sky-500/15 text-sky-300 ring-sky-500/30';
      default:
        return 'bg-slate-500/15 text-slate-300 ring-slate-500/30';
    }
  })();

  const label =
    score !== undefined && score !== null
      ? Number(score).toFixed(1)
      : (severity || 'UNKNOWN').toUpperCase();

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide ring-1 ${tone}`}
    >
      {label}
    </span>
  );
}

export default SeverityBadge;
