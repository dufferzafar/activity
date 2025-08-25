import type { HealthSummaryEntry } from '../types/health';

export async function loadHealthSummary(path: string = '/activity/data/health.history.summary.json'): Promise<HealthSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load Health summary: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  if (!Array.isArray(json)) {
    throw new Error('Invalid Health summary shape: expected an array');
  }
  const entries: HealthSummaryEntry[] = json
    .map((d: any) => ({
      date: String(d.date),
      energy_burned_kcal: Number(d.energy_burned_kcal),
      steps: Number(d.steps),
      walk_distance_meters: Number(d.walk_distance_meters)
    }))
    .filter((d) => Number.isFinite(d.energy_burned_kcal) && Number.isFinite(d.steps) && Number.isFinite(d.walk_distance_meters) && /^\d{4}-\d{2}-\d{2}$/.test(d.date));
  return entries;
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: HealthSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}


