export interface CallSummaryEntryRaw {
  date: string; // ISO YYYY-MM-DD
  incoming_count: number;
  outgoing_count: number;
  incoming_seconds: number;
  outgoing_seconds: number;
}

export interface CallSummaryEntry extends CallSummaryEntryRaw {
  total_count: number;
  total_seconds: number;
  total_minutes: number;
}


