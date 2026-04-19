<script lang="ts">
  import { syncState } from "$lib/stores/sync.svelte";
  import { CheckCircle2, AlertCircle, Circle } from "@lucide/svelte";

  function relativeTime(iso: string | null): string {
    if (!iso) return "never";
    const now = Date.now();
    const then = new Date(iso).getTime();
    const seconds = Math.max(0, Math.floor((now - then) / 1000));
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  }

  let label = $derived.by(() => {
    if (syncState.error) return `Error: ${syncState.error}`;
    if (!syncState.lastRunAt) return "No syncs yet";
    const r = syncState.lastReport;
    const total = r ? r.observationsWritten + r.summariesWritten : 0;
    return `Last sync ${relativeTime(syncState.lastRunAt)} · ${total} new file${total === 1 ? "" : "s"}`;
  });
</script>

<footer
  class="flex items-center gap-2 px-5 py-3 border-t text-xs"
  style="border-color: var(--color-border); color: var(--color-muted);"
>
  {#if syncState.error}
    <AlertCircle size={14} strokeWidth={2} style="color: var(--color-danger);" />
  {:else if syncState.lastRunAt}
    <CheckCircle2 size={14} strokeWidth={2} style="color: var(--color-success);" />
  {:else}
    <Circle size={14} strokeWidth={2} />
  {/if}
  <span>{label}</span>
</footer>
