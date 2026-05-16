import { CATEGORY_COLORS } from '../project-map/photoMarkerPaint';

export function categoryPercentages(counts: {
  green: number;
  yellow: number;
  red: number;
}): { greenPct: number; yellowPct: number; redPct: number } {
  const total = counts.green + counts.yellow + counts.red;
  if (total === 0) {
    return { greenPct: 0, yellowPct: 0, redPct: 0 };
  }
  return {
    greenPct: Math.round((counts.green / total) * 100),
    yellowPct: Math.round((counts.yellow / total) * 100),
    redPct: Math.round((counts.red / total) * 100),
  };
}

function Segment({ pct, color }: { pct: number; color: string }) {
  if (pct <= 0) return null;
  return (
    <div className="h-full" style={{ width: `${pct}%`, backgroundColor: color }} />
  );
}

export function DocumentationStatusBar({
  greenPct,
  yellowPct,
  redPct,
  className = 'h-2',
  widthClassName,
}: {
  greenPct: number;
  yellowPct: number;
  redPct: number;
  className?: string;
  widthClassName?: string;
}) {
  return (
    <div className={`flex overflow-hidden rounded-full ${className} ${widthClassName ?? ''}`}>
      <Segment pct={greenPct} color={CATEGORY_COLORS.green} />
      <Segment pct={yellowPct} color={CATEGORY_COLORS.yellow} />
      <Segment pct={redPct} color={CATEGORY_COLORS.red} />
    </div>
  );
}

export function DocumentationStatusBarFromCounts({
  counts,
  className = 'h-2',
  widthClassName,
}: {
  counts: { green: number; yellow: number; red: number };
  className?: string;
  widthClassName?: string;
}) {
  const { greenPct, yellowPct, redPct } = categoryPercentages(counts);
  return (
    <DocumentationStatusBar
      greenPct={greenPct}
      yellowPct={yellowPct}
      redPct={redPct}
      className={className}
      widthClassName={widthClassName}
    />
  );
}
