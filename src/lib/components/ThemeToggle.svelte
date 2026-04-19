<script lang="ts">
  import { Sun, Moon, Monitor } from "@lucide/svelte";
  import type { Theme } from "$lib/types";

  type Props = {
    value: Theme;
    onChange: (next: Theme) => void;
  };

  let { value, onChange }: Props = $props();

  function cycle() {
    const order: Theme[] = ["auto", "light", "dark"];
    const next = order[(order.indexOf(value) + 1) % order.length];
    onChange(next);
  }

  const label = $derived(
    value === "auto" ? "System" : value === "light" ? "Light" : "Dark",
  );
</script>

<button
  type="button"
  onclick={cycle}
  aria-label="Cycle theme: {label}"
  title="Theme: {label} (click to cycle)"
  class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors"
  style="background-color: var(--color-surface-elevated); border-color: var(--color-border); color: var(--color-text);"
>
  {#if value === "auto"}
    <Monitor size={14} strokeWidth={2} />
  {:else if value === "light"}
    <Sun size={14} strokeWidth={2} />
  {:else}
    <Moon size={14} strokeWidth={2} />
  {/if}
  <span class="hidden sm:inline">{label}</span>
</button>
