import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import type {
  SyncPreview,
  SyncProgress,
  SyncReport,
  SyncState,
} from "$lib/types";

export const syncState = $state<{
  running: boolean;
  progress: SyncProgress | null;
  lastReport: SyncReport | null;
  lastRunAt: string | null;
  error: string | null;
}>({
  running: false,
  progress: null,
  lastReport: null,
  lastRunAt: null,
  error: null,
});

export async function loadLastSync() {
  try {
    const s = await invoke<SyncState>("last_sync_state");
    syncState.lastReport = s.lastRunReport;
    syncState.lastRunAt = s.lastRunAt;
  } catch (e) {
    console.error("failed to load last sync state", e);
  }
}

export async function startSync(dbPath: string, vaultPath: string) {
  if (syncState.running) return;
  syncState.running = true;
  syncState.progress = null;
  syncState.error = null;
  try {
    const report = await invoke<SyncReport>("run_sync", {
      dbPath,
      vaultPath,
    });
    syncState.lastReport = report;
    syncState.lastRunAt = new Date().toISOString();
  } catch (e) {
    syncState.error = String(e);
  } finally {
    syncState.running = false;
    syncState.progress = null;
  }
}

export async function previewSync(dbPath: string): Promise<SyncPreview> {
  return await invoke<SyncPreview>("probe_sync", { dbPath });
}

export async function attachProgressListener(): Promise<UnlistenFn> {
  return await listen<SyncProgress>("sync:progress", (event) => {
    syncState.progress = event.payload;
  });
}
