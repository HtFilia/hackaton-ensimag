export interface BookEntry {
  price: number;
  quantity: number;
}

export interface BookSnapshot {
  bids: BookEntry[];
  asks: BookEntry[];
}

// Single-asset ou multi-asset
export type Snapshot = BookSnapshot | Record<string, BookSnapshot> | null;

export interface FixtureResult {
  fixture: string;
  passed: boolean;
  message: string;
  duration_ms: number;
  expected: Snapshot;
  got: Snapshot;
}

export type PalierStatus = "passed" | "failed" | "not_tested" | "error";

export interface LevelResult {
  status: PalierStatus;
  duration_ms: number;
  fixtures: FixtureResult[];
}

export interface StudentResults {
  team: string;
  updated_at: string | null;
  first_pass_times: Record<string, string>;
  levels: Record<string, LevelResult>;
}

export interface HackathonConfig {
  title: string;
  subtitle: string;
  end_time: string | null;
  timer_visible_by_default: boolean;
  total_paliers: number;
}
