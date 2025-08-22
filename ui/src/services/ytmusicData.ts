import type { YTMusicSummaryEntry } from '../types/ytmusic';

export async function loadSearchSummary(path: string = '/activity/data/ytmusic.search.summary.json'): Promise<YTMusicSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load YTMusic summary: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  if (!Array.isArray(json)) {
    throw new Error('Invalid YTMusic summary shape: expected an array');
  }
  const entries: YTMusicSummaryEntry[] = json
    .map((d: any) => ({ date: String(d.date), count: Number(d.count) }))
    .filter((d) => Number.isFinite(d.count) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  return entries;
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: YTMusicSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}


