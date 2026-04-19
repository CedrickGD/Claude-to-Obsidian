<script lang="ts">
  import { Settings as SettingsIcon } from "@lucide/svelte";
  import { config } from "$lib/stores/config.svelte";
  import {
    enable as enableAutostart,
    disable as disableAutostart,
  } from "@tauri-apps/plugin-autostart";

  async function onAutostartChange(e: Event) {
    const checked = (e.target as HTMLInputElement).checked;
    try {
      if (checked) await enableAutostart();
      else await disableAutostart();
      config.autostart = checked;
    } catch (err) {
      console.error("autostart toggle failed", err);
      (e.target as HTMLInputElement).checked = config.autostart;
    }
  }

  function onIntervalInput(e: Event) {
    const v = parseInt((e.target as HTMLInputElement).value || "0", 10);
    if (!isNaN(v) && v >= 1 && v <= 1440) {
      config.intervalMinutes = v;
    }
  }
</script>

<section
  class="rounded-xl border p-5"
  style="background-color: var(--color-surface-elevated); border-color: var(--color-border);"
>
  <div class="flex items-center gap-2 mb-4">
    <SettingsIcon size={16} strokeWidth={2} />
    <span class="text-sm font-medium">Sync settings</span>
  </div>

  <div class="flex items-center gap-3 mb-4">
    <label for="interval" class="text-sm">Every</label>
    <input
      id="interval"
      type="number"
      min="1"
      max="1440"
      value={config.intervalMinutes}
      oninput={onIntervalInput}
      class="w-20 rounded-lg border px-2 py-1.5 text-sm text-center"
      style="background-color: var(--color-surface); border-color: var(--color-border); color: var(--color-text);"
    />
    <span class="text-sm" style="color: var(--color-muted);">minutes</span>
  </div>

  <label class="flex items-center gap-3 mb-3 cursor-pointer">
    <input
      type="checkbox"
      bind:checked={config.scheduleEnabled}
      class="h-4 w-4 rounded accent-current"
      style="accent-color: var(--color-accent);"
    />
    <span class="text-sm">Run sync in background</span>
  </label>

  <label class="flex items-center gap-3 cursor-pointer">
    <input
      type="checkbox"
      checked={config.autostart}
      onchange={onAutostartChange}
      class="h-4 w-4 rounded"
      style="accent-color: var(--color-accent);"
    />
    <span class="text-sm">Launch at login</span>
  </label>
</section>
