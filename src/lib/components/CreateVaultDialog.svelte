<script lang="ts">
  import { open } from "@tauri-apps/plugin-dialog";
  import { invoke } from "@tauri-apps/api/core";
  import { FolderPlus, X } from "@lucide/svelte";

  type Props = {
    open: boolean;
    onCreated: (path: string) => void;
    onClose: () => void;
  };

  let { open: isOpen, onCreated, onClose }: Props = $props();
  let parentDir = $state("");
  let vaultName = $state("Claude Memories");
  let busy = $state(false);
  let error = $state<string | null>(null);

  $effect(() => {
    if (isOpen) {
      parentDir = "";
      vaultName = "Claude Memories";
      busy = false;
      error = null;
    }
  });

  async function pickParent() {
    const path = await open({
      directory: true,
      title: "Choose where to create the vault",
    });
    if (typeof path === "string") parentDir = path;
  }

  async function create() {
    busy = true;
    error = null;
    try {
      const created = await invoke<string>("create_vault", {
        parentDir,
        vaultName,
      });
      onCreated(created);
    } catch (e) {
      error = String(e);
    } finally {
      busy = false;
    }
  }

  let canCreate = $derived(
    parentDir.length > 0 && vaultName.trim().length > 0 && !busy,
  );
</script>

{#if isOpen}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    style="backdrop-filter: blur(4px);"
    onclick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}
    onkeydown={(e) => {
      if (e.key === "Escape") onClose();
    }}
    role="presentation"
    tabindex="-1"
  >
    <div
      class="w-full max-w-md rounded-2xl border p-6 shadow-2xl"
      style="background-color: var(--color-surface-elevated); border-color: var(--color-border);"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-vault-title"
      tabindex="-1"
    >
      <div class="flex items-center justify-between mb-5">
        <div class="flex items-center gap-2">
          <FolderPlus size={18} strokeWidth={2} />
          <h2 id="create-vault-title" class="text-lg font-semibold">
            Create new vault
          </h2>
        </div>
        <button
          type="button"
          onclick={onClose}
          aria-label="Close"
          class="rounded-lg p-1 hover:opacity-70 transition-opacity"
          style="color: var(--color-muted);"
        >
          <X size={18} strokeWidth={2} />
        </button>
      </div>

      <div class="space-y-4">
        <div>
          <label
            for="parent-dir"
            class="text-sm font-medium block mb-1.5"
          >Location</label>
          <div class="flex gap-2">
            <input
              id="parent-dir"
              type="text"
              readonly
              value={parentDir}
              placeholder="Pick a parent folder…"
              class="flex-1 rounded-lg border px-3 py-2 text-sm min-w-0 truncate"
              style="background-color: var(--color-surface); border-color: var(--color-border); color: var(--color-text);"
            />
            <button
              type="button"
              onclick={pickParent}
              class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors hover:opacity-90"
              style="background-color: var(--color-surface); border-color: var(--color-border-strong); color: var(--color-text);"
            >Browse</button>
          </div>
        </div>

        <div>
          <label
            for="vault-name"
            class="text-sm font-medium block mb-1.5"
          >Vault name</label>
          <input
            id="vault-name"
            type="text"
            bind:value={vaultName}
            class="w-full rounded-lg border px-3 py-2 text-sm"
            style="background-color: var(--color-surface); border-color: var(--color-border); color: var(--color-text);"
          />
          <p class="mt-1.5 text-xs" style="color: var(--color-muted);">
            We'll create <code>.obsidian/</code>, <code>Claude Memories/</code>, and a welcome note.
          </p>
        </div>

        {#if error}
          <p
            class="rounded-lg border px-3 py-2 text-sm"
            style="color: var(--color-danger); border-color: var(--color-danger); background-color: color-mix(in srgb, var(--color-danger) 8%, transparent);"
          >{error}</p>
        {/if}

        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onclick={onClose}
            class="rounded-lg px-4 py-2 text-sm font-medium transition-colors hover:opacity-70"
            style="color: var(--color-muted);"
          >Cancel</button>
          <button
            type="button"
            onclick={create}
            disabled={!canCreate}
            class="rounded-lg px-4 py-2 text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
            style="background-color: var(--color-accent); color: white;"
          >{busy ? "Creating…" : "Create vault"}</button>
        </div>
      </div>
    </div>
  </div>
{/if}
