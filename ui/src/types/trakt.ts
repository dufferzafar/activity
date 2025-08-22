export interface GenreCount {
  name: string;
  count: number;
}

export interface RuntimeSummaryEntry {
  date: string; // ISO YYYY-MM-DD
  total_runtime: number; // minutes
  genres: GenreCount[];
  subgenres: GenreCount[];
} 