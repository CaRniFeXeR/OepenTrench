export function ReportStatValue({
  absolute,
  percentage,
  suffix,
}: {
  absolute: number;
  percentage: number;
  suffix?: string;
}) {
  return (
    <div className="shrink-0 text-right tabular-nums">
      <p className="text-xl font-bold leading-none text-slate-900">{absolute}</p>
      <p className="mt-0.5 text-xs text-slate-600">
        {percentage}%
        {suffix ? ` · ${suffix}` : ''}
      </p>
    </div>
  );
}
