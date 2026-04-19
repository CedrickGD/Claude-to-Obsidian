<script lang="ts">
  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { Play, Zap, Eye, Sparkles } from "@lucide/svelte";

  import {
    config,
    loadConfig,
    saveConfig,
    isLoaded,
  } from "$lib/stores/config.svelte";
  import {
    syncState,
    loadLastSync,
    startSync,
    previewSync,
    attachProgressListener,
  } from "$lib/stores/sync.svelte";
  import { applyTheme, watchSystemTheme } from "$lib/stores/theme.svelte";
  import type { AutoDetectResult } from "$lib/types";

  import PathCard from "$lib/components/PathCard.svelte";
  import SettingsCard from "$lib/components/SettingsCard.svelte";
  import ThemeToggle from "$lib/components/ThemeToggle.svelte";
  import SyncProgress from "$lib/components/SyncProgress.svelte";
  import LastSyncStatus from "$lib/components/LastSyncStatus.svelte";
  import OpenInObsidian from "$lib/components/OpenInObsidian.svelte";
  import CreateVaultDialog from "$lib/components/CreateVaultDialog.svelte";

  let dbStats = $state<string | null>(null);
  let previewText = $state<string | null>(null);
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let showCreateVault = $state(false);
  let detectStatus = $state<string | null>(null);
  let detectStatusTimer: ReturnType<typeof setTimeout> | null = null;

  async function attemptAutoDetect() {
    if (config.dbPath && config.vaultPath) return;
    try {
      const result = await invoke<AutoDetectResult>("auto_detect");
      if (!config.dbPath && result.dbPath) config.dbPath = result.dbPath;
      if (!config.vaultPath && result.vaultPath) config.vaultPath = result.vaultPath;
    } catch (e) {
      console.warn("auto-detect failed", e);
    }
  }

  function flashDetectStatus(msg: string) {
    detectStatus = msg;
    if (detectStatusTimer) clearTimeout(detectStatusTimer);
    detectStatusTimer = setTimeout(() => (detectStatus = null), 3000);
  }

  async function runAutoDetect() {
    try {
      const result = await invoke<AutoDetectResult>("auto_detect");
      const changes: string[] = [];
      if (result.dbPath && result.dbPath !== config.dbPath) {
        config.dbPath = result.dbPath;
        changes.push("database");
      }
      if (result.vaultPath && result.vaultPath !== config.vaultPath) {
        config.vaultPath = result.vaultPath;
        changes.push("vault");
      }
      if (changes.length === 0) {
        if (!result.dbPath && !result.vaultPath) {
          flashDetectStatus("Nothing detected — pick paths manually.");
        } else {
          flashDetectStatus("Paths already up to date");
        }
      } else {
        flashDetectStatus(`Detected ${changes.join(" + ")}`);
      }
    } catch (e) {
      flashDetectStatus(`Detection failed: ${e}`);
    }
  }

  onMount(() => {
    let unlistenProgress: (() => void) | null = null;
    let unwatchTheme: (() => void) | null = null;

    (async () => {
      await loadConfig();
      applyTheme(config.theme);
      unwatchTheme = watchSystemTheme(() => config.theme);
      await loadLastSync();
      unlistenProgress = await attachProgressListener();
      await attemptAutoDetect();
    })();

    return () => {
      unlistenProgress?.();
      unwatchTheme?.();
    };
  });

  // Debounced autosave on any config change
  $effect(() => {
    void config.dbPath;
    void config.vaultPath;
    void config.intervalMinutes;
    void config.theme;
    void config.autostart;
    void config.scheduleEnabled;
    if (!isLoaded()) return;
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => saveConfig().catch(console.error), 400);
  });

  // Re-apply theme on change
  $effect(() => {
    applyTheme(config.theme);
  });

  // Refresh pending-sync counts whenever DB path changes
  $effect(() => {
    const path = config.dbPath;
    if (!path) {
      dbStats = null;
      return;
    }
    previewSync(path)
      .then((p) => {
        const pending = p.newObservations + p.newSummaries;
        dbStats =
          pending === 0
            ? "Up to date"
            : `${p.newObservations} new observations · ${p.newSummaries} new summaries pending`;
      })
      .catch(() => {
        dbStats = null;
      });
  });

  async function onPreview() {
    if (!config.dbPath) return;
    try {
      const p = await previewSync(config.dbPath);
      previewText = `Ready to sync ${p.newObservations} observations and ${p.newSummaries} summaries`;
    } catch (e) {
      previewText = `Preview failed: ${e}`;
    }
  }

  async function onSyncNow() {
    if (!config.dbPath || !config.vaultPath) return;
    previewText = null;
    await startSync(config.dbPath, config.vaultPath);
  }

  async function onApply() {
    config.scheduleEnabled = true;
    await saveConfig();
  }

  let canSync = $derived(
    !!config.dbPath && !!config.vaultPath && !syncState.running,
  );
  let canPreview = $derived(!!config.dbPath && !syncState.running);
</script>

<div class="min-h-screen flex flex-col">
  <div class="flex-1 w-full max-w-2xl mx-auto px-8 py-10">
    <header class="flex items-center justify-between mb-8">
      <h1 class="text-3xl font-semibold tracking-tight">
        Claude <span style="color: var(--color-muted);">→</span> Obsidian
      </h1>
      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={runAutoDetect}
          title="Auto-detect Claude memory DB + Obsidian vault"
          class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors hover:opacity-90"
          style="background-color: var(--color-surface-elevated); border-color: var(--color-border); color: var(--color-text);"
        >
          <Sparkles size={14} strokeWidth={2} />
          <span class="hidden sm:inline">Auto-detect</span>
        </button>
        <ThemeToggle
          value={config.theme}
          onChange={(next) => (config.theme = next)}
        />
      </div>
    </header>

    {#if detectStatus}
      <div
        class="mb-4 rounded-lg border px-4 py-2 text-sm transition-opacity"
        style="background-color: var(--color-surface-elevated); border-color: var(--color-border); color: var(--color-muted);"
      >
        {detectStatus}
      </div>
    {/if}

    <div class="space-y-4">
      <PathCard
        kind="db"
        label="Claude memory database"
        value={config.dbPath}
        stats={dbStats}
        placeholder="Select claude-mem.db"
        onChange={(p) => (config.dbPath = p)}
      />

      <PathCard
        kind="vault"
        label="Obsidian vault"
        value={config.vaultPath}
        placeholder="Select vault folder"
        extraAction={{
          label: "Create new vault…",
          onClick: () => (showCreateVault = true),
        }}
        onChange={(p) => (config.vaultPath = p)}
      />

      <SettingsCard />

      <SyncProgress />

      {#if previewText}
        <div
          class="rounded-xl border p-4 text-sm"
          style="background-color: var(--color-surface-elevated); border-color: var(--color-border);"
        >
          {previewText}
        </div>
      {/if}

      <div class="grid grid-cols-3 gap-2 mt-2">
        <button
          type="button"
          onclick={onPreview}
          disabled={!canPreview}
          class="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          style="background-color: var(--color-surface-elevated); border-color: var(--color-border-strong); color: var(--color-text);"
        >
          <Eye size={14} strokeWidth={2} />
          Preview
        </button>

        <button
          type="button"
          onclick={onSyncNow}
          disabled={!canSync}
          class="flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          style="background-color: var(--color-surface-elevated); border-color: var(--color-border-strong); color: var(--color-text);"
        >
          <Play size={14} strokeWidth={2} />
          Sync now
        </button>

        <OpenInObsidian vaultPath={config.vaultPath} />
      </div>

      <button
        type="button"
        onclick={onApply}
        disabled={!canSync}
        class="w-full flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold transition-colors hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        style="background-color: var(--color-accent); color: white;"
      >
        <Zap size={14} strokeWidth={2.5} />
        Apply & automate
      </button>
    </div>
  </div>

  <LastSyncStatus />
</div>

<CreateVaultDialog
  open={showCreateVault}
  onCreated={(p) => {
    config.vaultPath = p;
    showCreateVault = false;
  }}
  onClose={() => (showCreateVault = false)}
/>

