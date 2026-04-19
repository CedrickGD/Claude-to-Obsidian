export type Theme = "auto" | "light" | "dark";

export interface Config {
  dbPath: string | null;
  vaultPath: string | null;
  intervalMinutes: number;
  theme: Theme;
  autostart: boolean;
  scheduleEnabled: boolean;
}

export interface SyncReport {
  observationsWritten: number;
  summariesWritten: number;
  durationMs: number;
}

export interface SyncPreview {
  newObservations: number;
  newSummaries: number;
}

export interface SyncState {
  lastObservationId: number;
  lastSummaryId: number;
  lastRunAt: string | null;
  lastRunReport: SyncReport | null;
}

export interface AutoDetectResult {
  dbPath: string | null;
  vaultPath: string | null;
}

export interface SyncProgress {
  kind: "observation" | "summary";
  current: number;
  total: number;
}

export const defaultConfig = (): Config => ({
  dbPath: null,
  vaultPath: null,
  intervalMinutes: 15,
  theme: "auto",
  autostart: false,
  scheduleEnabled: false,
});
