<script lang="ts">
  import { openUrl } from "@tauri-apps/plugin-opener";
  import { ExternalLink } from "@lucide/svelte";

  type Props = { vaultPath: string | null };
  let { vaultPath }: Props = $props();

  async function openInObsidian() {
    if (!vaultPath) return;
    const encoded = encodeURIComponent(vaultPath);
    try {
      await openUrl(`obsidian://open?path=${encoded}`);
    } catch {
      // Obsidian not installed or protocol unhandled — open folder in file manager
      try {
        await openUrl(`file://${vaultPath}`);
      } catch (e) {
        console.error("failed to open vault", e);
      }
    }
  }
</script>

<button
  type="button"
  onclick={openInObsidian}
  disabled={!vaultPath}
  class="flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
  style="background-color: var(--color-surface-elevated); border-color: var(--color-border-strong); color: var(--color-text);"
>
  <ExternalLink size={14} strokeWidth={2} />
  Open in Obsidian
</button>
