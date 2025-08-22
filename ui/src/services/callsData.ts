import type { CallSummaryEntry, CallSummaryEntryRaw } from '../types/calls';

export async function loadCallsSummary(path: string = '/activity/data/calls.history.summary.json'): Promise<CallSummaryEntry[]> {
  const response = await fetch(path, { cache: 'no-cache' });
  if (!response.ok) {
    throw new Error(`Failed to load Calls summary: ${response.status} ${response.statusText}`);
  }
  const json = (await response.json()) as unknown;
  if (!Array.isArray(json)) {
    throw new Error('Invalid Calls summary shape: expected an array');
  }

  const entries: CallSummaryEntry[] = json
    .map((d: any) => normalizeCallEntry(d))
    .filter((d): d is CallSummaryEntry =>
      !!d && Number.isFinite(d.total_seconds) && Number.isFinite(d.total_count) && /^\d{4}-\d{2}-\d{2}$/.test(d.date),
    );
  return entries;
}

function normalizeCallEntry(d: any): CallSummaryEntry | null {
  if (!d) return null;
  const raw: CallSummaryEntryRaw = {
    date: String(d.date),
    incoming_count: Number(d.incoming_count ?? 0),
    outgoing_count: Number(d.outgoing_count ?? 0),
    incoming_seconds: Number(d.incoming_seconds ?? 0),
    outgoing_seconds: Number(d.outgoing_seconds ?? 0),
  };
  const total_count = (Number.isFinite(raw.incoming_count) ? raw.incoming_count : 0)
    + (Number.isFinite(raw.outgoing_count) ? raw.outgoing_count : 0);
  const total_seconds = (Number.isFinite(raw.incoming_seconds) ? raw.incoming_seconds : 0)
    + (Number.isFinite(raw.outgoing_seconds) ? raw.outgoing_seconds : 0);
  const total_minutes = Math.round(total_seconds / 60);
  return { ...raw, total_count, total_seconds, total_minutes };
}

export function getYearFromISO(isoDate: string): number {
  return new Date(isoDate + 'T00:00:00Z').getUTCFullYear();
}

export function groupYears(entries: CallSummaryEntry[]): number[] {
  const years = new Set<number>();
  for (const e of entries) {
    years.add(getYearFromISO(e.date));
  }
  return Array.from(years).sort((a, b) => a - b);
}


