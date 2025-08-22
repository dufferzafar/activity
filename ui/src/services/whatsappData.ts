import type { WhatsAppSummaryEntry } from '../types/whatsapp';

export async function loadWhatsAppSummary(path: string = '/activity/data/whatsapp.history.summary.json'): Promise<WhatsAppSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load WhatsApp summary: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  if (!Array.isArray(json)) {
    throw new Error('Invalid WhatsApp summary shape: expected an array');
  }
  const entries: WhatsAppSummaryEntry[] = json
    .map((d: any) => ({ date: String(d.date), msgs_sent: Number(d.msgs_sent ?? 0) }))
    .filter((d) => Number.isFinite(d.msgs_sent) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  return entries;
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: WhatsAppSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}


