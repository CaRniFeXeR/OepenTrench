const MISMATCH_FIELD_LABELS: Record<string, string> = {
  duct: 'Duct',
  ruler: 'Ruler',
  domain: 'Domain',
  gps: 'GPS',
  privacy: 'Privacy',
  category: 'Category',
};

export function mismatchFieldLabel(key: string): string {
  return MISMATCH_FIELD_LABELS[key] ?? key;
}
