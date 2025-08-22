import type { RuntimeSummaryEntry, GenreCount } from '../types/trakt';
import { getYearFromISO } from './traktRuntimeData';

export interface MonthlyGenres {
  year: number;
  month: number; // 1-12
  genres: GenreCount[]; // sorted desc by count
}

export function aggregateGenresByMonth(entries: RuntimeSummaryEntry[]): MonthlyGenres[] {
  const key = (y: number, m: number) => `${y}-${m}`;

  const map = new Map<string, Map<string, number>>();

  for (const e of entries) {
    const year = getYearFromISO(e.date);
    const month = new Date(e.date + 'T00:00:00Z').getUTCMonth() + 1; // 1-12
    const km = key(year, month);
    if (!map.has(km)) map.set(km, new Map());
    const genreMap = map.get(km)!;

    for (const g of e.genres ?? []) {
      const prev = genreMap.get(g.name) ?? 0;
      genreMap.set(g.name, prev + (Number.isFinite(g.count) ? g.count : 0));
    }
  }

  const monthly: MonthlyGenres[] = [];
  for (const [k, genreMap] of map) {
    const [ys, ms] = k.split('-');
    const year = Number(ys);
    const month = Number(ms);
    const genres: GenreCount[] = Array.from(genreMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
    monthly.push({ year, month, genres });
  }

  // Sort by year asc, then month asc
  monthly.sort((a, b) => (a.year - b.year) || (a.month - b.month));
  return monthly;
}

export function aggregateSubgenresByMonth(entries: RuntimeSummaryEntry[], limit: number = 5): MonthlyGenres[] {
  const key = (y: number, m: number) => `${y}-${m}`;

  const map = new Map<string, Map<string, number>>();

  for (const e of entries) {
    const year = getYearFromISO(e.date);
    const month = new Date(e.date + 'T00:00:00Z').getUTCMonth() + 1; // 1-12
    const km = key(year, month);
    if (!map.has(km)) map.set(km, new Map());
    const subMap = map.get(km)!;

    for (const g of e.subgenres ?? []) {
      const prev = subMap.get(g.name) ?? 0;
      subMap.set(g.name, prev + (Number.isFinite(g.count) ? g.count : 0));
    }
  }

  const monthly: MonthlyGenres[] = [];
  for (const [k, subMap] of map) {
    const [ys, ms] = k.split('-');
    const year = Number(ys);
    const month = Number(ms);
    const genres: GenreCount[] = Array.from(subMap.entries())
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, Math.max(0, limit));
    monthly.push({ year, month, genres });
  }

  monthly.sort((a, b) => (a.year - b.year) || (a.month - b.month));
  return monthly;
}

export function hashHue(input: string): number {
  let h = 0;
  for (let i = 0; i < input.length; i++) {
    h = (h * 31 + input.charCodeAt(i)) >>> 0;
  }
  return h % 360;
}

export function computeFontSize(count: number, min: number, max: number, minSize = 12, maxSize = 28): number {
  if (max <= min) return Math.round((minSize + maxSize) / 2);
  const t = (count - min) / (max - min);
  return Math.round(minSize + t * (maxSize - minSize));
} 