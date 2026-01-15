export function formatDomainLabel(domain: string | undefined | null): string {
  if (!domain) return '';
  const map: Record<string, string> = {
    legal_registration: 'Legal Registration',
    tax_compliance: 'Tax Compliance',
    auditing_reporting: 'Legal Auditing',
    licensing: 'Licensing',
    tech_ip_compliance: 'Tech/IP Compliance',
    special_zones: 'Special Zones',
    startup_incentives: 'Startup Incentives',
  };
  if (map[domain]) return map[domain];
  // Fallback: convert snake_case to Title Case
  return domain
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
    .replace(/(^|\s)\S/g, (c) => c.toUpperCase());
}

export function getDomainKeyFromProc(proc: any): string {
  const d = (proc?.domain ?? '').toString().trim();
  if (d) return d;
  const name = (proc?.procedure_name || proc?.name || '').toString().toLowerCase();
  if (!name) return 'other';
  if (name.includes('tax')) return 'tax_compliance';
  if (name.includes('label')) return 'startup_incentives';
  if (name.includes('tech') || name.includes('ip') || name.includes('data')) return 'tech_ip_compliance';
  if (name.includes('register') || name.includes('sarl') || name.includes('sa') || name.includes('commercial')) return 'legal_registration';
  if (name.includes('license')) return 'licensing';
  if (name.includes('audit') || name.includes('report')) return 'auditing_reporting';
  if (name.includes('zone')) return 'special_zones';
  return 'other';
}
