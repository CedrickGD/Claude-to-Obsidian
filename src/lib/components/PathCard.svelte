<script lang="ts">
  import { open } from "@tauri-apps/plugin-dialog";
  import { Database, FolderOpen } from "@lucide/svelte";

  type Props = {
    kind: "db" | "vault";
    label: string;
    value: string | null;
    placeholder?: string;
    stats?: string | null;
    extraAction?: { label: string; onClick: () => void } | null;
    onChange: (path: string) => void;
  };

  let {
    kind,
    label,
    value,
    placeholder = "Not selected",
    stats = null,
    extraAction = null,
    onChange,
  }: Props = $props();

  async function browse() {
    const path = await open(
      kind === "db"
        ? {
            multiple: false,
            directory: false,
            filters: [{ name: "SQLite DB", extensions: ["db"] }],
            title: "Select claude-mem.db",
          }
        : {
            multiple: false,
            directory: true,
            title: "Select Obsidian vault folder",
          },
    );
    if (typeof path === "string") onChange(path);
  }
</script>

<section
  class="rounded-xl border p-5 transition-colors"
  style="background-color: var(--color-surface-elevated); border-color: var(--color-border);"
>
  <div class="flex items-center gap-2 mb-3">
    {#if kind === "db"}
      <Database size={16} strokeWidth={2} />
    {:else}
      <FolderOpen size={16} strokeWidth={2} />
    {/if}
    <span class="text-sm font-medium">{label}</span>
  </div>

  <div class="flex gap-2">
    <input
      type="text"
      readonly
      value={value ?? ""}
      {placeholder}
      class="flex-1 rounded-lg border px-3 py-2 text-sm min-w-0 truncate"
      style="background-color: var(--color-surface); border-color: var(--color-border); color: var(--color-text);"
    />
    <button
      type="button"
      onclick={browse}
      class="rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:opacity-90"
      style="background-color: var(--color-surface); border-color: var(--color-border-strong); color: var(--color-text);"
    >
      Browse
    </button>
  </div>

  {#if stats}
    <p class="mt-2 text-xs" style="color: var(--color-muted);">{stats}</p>
  {/if}

  {#if extraAction}
    <button
      type="button"
      onclick={extraAction.onClick}
      class="mt-2 text-xs underline-offset-2 hover:underline"
      style="color: var(--color-accent);"
    >
      {extraAction.label}
    </button>
  {/if}
</section>
