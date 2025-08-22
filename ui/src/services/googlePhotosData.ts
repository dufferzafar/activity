import type { GooglePhotosSummaryEntry } from '../types/googlephotos';

export async function loadPhotosSummary(path: string = '/activity/data/googlephotos.summary.json'): Promise<GooglePhotosSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load Google Photos summary: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  let entries: GooglePhotosSummaryEntry[] = [];
  if (Array.isArray(json)) {
    entries = json
      .map((d: any) => ({ date: String(d.date), count: Number(d.count) }))
      .filter((d) => Number.isFinite(d.count) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  } else if (json && typeof json === 'object') {
    // Support date-keyed object map: { "YYYY-MM-DD": number }
    entries = Object.entries(json as Record<string, unknown>)
      .map(([date, count]) => ({ date: String(date), count: Number(count) }))
      .filter((d) => Number.isFinite(d.count) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  } else {
    throw new Error('Invalid Google Photos summary shape: expected array or date-keyed object');
  }
  return entries;
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: GooglePhotosSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}


