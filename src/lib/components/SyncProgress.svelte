<script lang="ts">
  import { syncState } from "$lib/stores/sync.svelte";
  import { Loader2 } from "@lucide/svelte";

  let pct = $derived.by(() => {
    const p = syncState.progress;
    if (!p || p.total === 0) return 0;
    return Math.round((p.current / p.total) * 100);
  });

  let text = $derived.by(() => {
    const p = syncState.progress;
    if (!p) return syncState.running ? "Preparing sync…" : "";
    const word = p.kind === "observation" ? "observations" : "summaries";
    return `Syncing ${word}  ${p.current} / ${p.total}`;
  });
</script>

{#if syncState.running}
  <div
    class="rounded-xl border p-4"
    style="background-color: var(--color-surface-elevated); border-color: var(--color-border);"
  >
    <div class="flex items-center gap-3 mb-2">
      <Loader2 size={14} strokeWidth={2} class="animate-spin" />
      <span class="text-sm flex-1">{text}</span>
      <span class="text-sm tabular-nums" style="color: var(--color-muted);"
        >{pct}%</span
      >
    </div>
    <div
      class="h-1.5 overflow-hidden rounded-full"
      style="background-color: var(--color-border);"
    >
      <div
        class="h-full transition-all duration-150"
        style="background-color: var(--color-accent); width: {pct}%;"
      ></div>
    </div>
  </div>
{/if}
