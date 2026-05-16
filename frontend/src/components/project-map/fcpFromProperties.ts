export function fcpIdFromProperties(props: Record<string, unknown> | null): string | null {
  if (!props) return null;
  const asOop = props.asOop;
  if (asOop != null) return String(asOop);
  return null;
}

export function fcpLabelFromProperties(props: Record<string, unknown> | null): string {
  if (!props) return 'FCP';
  const label = props.kmlDescriptionSimple;
  if (label != null && String(label).trim()) return String(label);
  const name = props.kmlName ?? props.name;
  if (name != null && String(name).trim()) return String(name);
  return 'FCP';
}

export function fcpCodeFromLabel(label: string): string {
  const token = label.trim().split(/\s+/)[0];
  return token || label;
}

export function fcpCodeFromProperties(props: Record<string, unknown> | null): string {
  const label = fcpLabelFromProperties(props);
  return fcpCodeFromLabel(label);
}
