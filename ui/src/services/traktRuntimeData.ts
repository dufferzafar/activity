import type { RuntimeSummaryEntry } from '../types/trakt';

export async function loadRuntimeSummary(path: string = '/activity/data/trakt.history.summary.json'): Promise<RuntimeSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load summary data: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  if (!Array.isArray(json)) {
    throw new Error('Invalid summary data shape: expected an array');
  }
  // Basic runtime validation and filtering
  const entries: RuntimeSummaryEntry[] = json
    .map((d: any) => ({
      date: String(d.date),
      total_runtime: Number(d.total_runtime),
      genres: Array.isArray(d.genres) ? d.genres : [],
      subgenres: Array.isArray(d.subgenres) ? d.subgenres : [],
    }))
    .filter((d) => Number.isFinite(d.total_runtime) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  return entries;
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: RuntimeSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}

export function filterEntriesByYear(entries: RuntimeSummaryEntry[], year: number): RuntimeSummaryEntry[] {
  return entries.filter((e) => getYearFromISO(e.date) === year);
}

export function getMaxRuntime(entries: RuntimeSummaryEntry[]): number {
  return entries.reduce((max, e) => (e.total_runtime > max ? e.total_runtime : max), 0);
} 