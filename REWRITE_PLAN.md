# Claude-to-Obsidian — Rewrite Plan (Tauri 2 + Svelte 5)

Goal: replace the Python/Tkinter implementation in `Claude-to-Obsidian/` with a native Tauri 2 desktop app. Rust owns the sync engine, SQLite reads, markdown writes, scheduling. Svelte 5 + Tailwind v4 + shadcn-svelte owns the UI, aiming for a Windows 11 Fluent-adjacent aesthetic with dark/light themes.

**Targets: Windows + macOS.** Both platforms in the same codebase and the same release. No Linux bundles for v1 (code still stays Linux-compatible — just no shipping binary).

---

## Implementation progress (2026-04-19)

**Phases 1–6 are code-complete.** Remaining: Phase 7 (logo/icons/bundling) and Phase 8 (verification sweep).

| Phase | Status | Notes |
|---|---|---|
| 1 — Scaffold | Done | SvelteKit + adapter-static (not plain Svelte; Tauri's default template switched to SvelteKit). Tailwind v4 wired. `shadcn-svelte init` deferred (requires interactive preset pick) — components are hand-rolled against the CSS var token system. |
| 2 — Sync engine | Done | `src-tauri/src/{error,sync/mod,sync/observations,sync/summaries}.rs`. rusqlite 0.39 bundled. Progress events via `app.emit("sync:progress")`. |
| 3 — Config + auto-detect | Done | `config.rs` (plugin-store) + `autodetect.rs` (cross-platform via `dirs`) + `vault.rs` (create-vault command). |
| 4 — Main UI | Done | Fluent-inspired tokens in `src/app.css`. 6 components. Debounced autosave, Auto/Light/Dark theme with OS follow + FOUC guard. |
| 5 — Create-vault dialog | Done | `CreateVaultDialog.svelte` modal with validation, error surfacing, Escape/overlay-click close. Full 5-step onboarding wizard deferred — not needed for feature parity. |
| 6 — Scheduler | Done | `scheduler.rs` with Tokio interval loop; reads config each tick so changes apply without restart. Autostart wired via plugin checkbox. |
| 7 — Polish | Not started | Logo SVG drafted in §7.1; needs rasterization + `pnpm tauri icon`. macOS bundle config in `tauri.conf.json` already set. |
| 8 — Verification | Not started | Requires the MSVC environment caveat (below) to be resolved before `tauri dev` / `tauri build` can run. |

### MSVC environment caveat

The user's VS 2025 Insiders install has a **non-standard lib layout** — `msvcrt.lib` lives only in `VC/Tools/MSVC/<ver>/lib/onecore/x64/` rather than the expected `lib/x64/`. Result: `cargo check` / `cargo build` / `pnpm tauri dev` all fail at the link step with `LNK1104: msvcrt.lib cannot be opened`.

**Stopgap:** `scripts/cargo-msvc.bat` wraps cargo with `vcvars64.bat` and prepends the `onecore/x64` path to `LIB`. Gets past the msvcrt linker error, but then hits `cc-rs` failures compiling C++ (`vswhom-sys`, status 2, empty stderr) — suggesting the VS C++ Build Tools install is incomplete in other ways too.

**Durable fix:** Reinstall Visual Studio or install the standalone **Build Tools for Visual Studio 2022** (https://visualstudio.microsoft.com/visual-cpp-build-tools/), selecting the **Desktop development with C++** workload. That places `msvcrt.lib` and the rest of the CRT in the standard `lib/x64/` path, and `cc-rs` will find a complete compiler. Once that's done, `pnpm tauri dev` should Just Work from any shell.

Once the env is fixed, Phase 2 onward can be verified by running `pnpm tauri dev` and exercising the UI end-to-end.

---

## Feature scope

### Parity with the Python version
- Pick `claude-mem.db` (SQLite) and Obsidian vault folder
- Auto-detect both (Claude DB at `~/.claude-mem/claude-mem.db`; Obsidian config in `%APPDATA%/obsidian/obsidian.json` on Windows, `~/Library/Application Support/obsidian/obsidian.json` on macOS)
- Configurable sync interval (minutes)
- Manual "Sync Now" button
- "Apply & Automate" — schedule periodic background sync
- Dark/light theme toggle (now also "Auto / follow OS")
- Status feedback

### New in this rewrite
- **First-run onboarding wizard** — 5 steps: welcome → find Claude memories → choose or create vault → preview → automation
- **Create new Obsidian vault** — in-app wizard creates an Obsidian-compatible folder (`.obsidian/`, `Claude Memories/{Observations,Summaries}/`, a friendly `Welcome.md`)
- **Open in Obsidian** — one-click deep link (`obsidian://open?path=...`) with file-manager fallback if Obsidian isn't installed
- **Dry-run preview** — shows `"Ready to sync 15 new observations and 3 new summaries"` before committing writes
- **Live sync progress** — progress bar + per-item counter driven by `app.emit("sync:progress")`
- **Last-sync status** — footer line "✓ Last sync 3 min ago · 12 new files"
- **Autostart on login** — checkbox, powered by `tauri-plugin-autostart`
- **Native theme follows OS** — Auto mode tracks Windows / macOS appearance changes live

---

## Locked design decisions (from Phase 0 research)

| Area | Decision | Why |
|---|---|---|
| Frontend framework | Plain Svelte 5 + Vite (no SvelteKit) | Single-page desktop app; SvelteKit routing is overkill |
| Reactivity | Runes only (`$state`, `$derived`, `$effect`, `$props`, `$bindable`) | Svelte 5 standard; shared state via `.svelte.ts` modules |
| Styling | Tailwind v4 (CSS-first, no config file) | Modern idiom, dark-mode variant via `@custom-variant` |
| Components | shadcn-svelte on Bits UI v2 primitives | Copy-paste components you own, runes-native |
| Icons | `@lucide/svelte` (fallback `@iconify/svelte` with Fluent set) | Tree-shaken, Svelte 5 ready |
| Font stack | `"Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", Inter, system-ui` with `font-optical-sizing: auto` | Native Win11 font, Inter fallback for non-Windows |
| SQLite | `rusqlite 0.39` with `bundled` feature | User-picked DB path rules out sqlx macros; simpler than tauri-plugin-sql |
| Scheduling | In-process Tokio interval + `tauri-plugin-autostart` | Avoids `schtasks`/UAC entirely; portable; auto-launches on login |
| File I/O | All reads/writes in Rust `#[tauri::command]`s | Smaller capability surface; no arbitrary-path `fs:scope` gymnastics |
| Config persistence | `tauri-plugin-store` | Idiomatic, cross-platform, one-liner from JS |
| External URL / file open | `tauri-plugin-opener` | For `obsidian://` deep link + file-manager fallback |
| Cross-platform paths | `dirs` crate throughout | `config_dir()` returns `%APPDATA%` on Windows, `~/Library/Application Support` on macOS, `~/.config` on Linux — no platform forks needed |
| Error flow | `thiserror` `AppError` + hand-written `Serialize` → stringified | Official Tauri pattern |
| Progress updates | `app.emit("sync:progress", payload)` → `listen()` in `$effect` | Streams bulk operations to UI |
| Window theme | `tauri.conf.json` `"theme": null` (follow OS) + manual override | Native immersive dark title bar on Windows |
| Validation | `$derived` predicates (no library) | Two fields — no Zod/Valibot needed |
| Autosave | `$effect` + 400 ms `setTimeout` + `$state.snapshot` | Coalesces bursts, strips proxy before `invoke` |

**Anti-patterns to avoid** (these are not in current Tauri 2 / Svelte 5):
- `import { invoke } from '@tauri-apps/api/tauri'` — wrong path; v2 is `@tauri-apps/api/core`
- `on:click` handler directive — Svelte 5 uses `onclick={}` prop
- `export let foo` component props — Svelte 5 uses `let { foo } = $props()`
- `$: derived = expr` reactive declarations — Svelte 5 uses `let derived = $derived(expr)`
- Tauri v1 `allowlist` in `tauri.conf.json` — v2 uses `capabilities/*.json` files
- `planif` crate for Windows scheduling — archived as of 2024-07; skipped entirely
- Compile-time SQL macros (`sqlx::query!`) on user-provided DB paths — impossible; we picked `rusqlite`

---

## Phase 0 — Documentation Discovery (COMPLETE)

Three parallel research agents produced the allowed-APIs list above. Full transcripts archived in this plan's design table. Key source URLs per area:

- **Tauri 2 core**: https://v2.tauri.app/start/create-project/, https://v2.tauri.app/develop/calling-rust/, https://v2.tauri.app/security/capabilities/
- **Tauri 2 plugins**: https://v2.tauri.app/plugin/dialog/, https://v2.tauri.app/plugin/store/, https://v2.tauri.app/plugin/autostart/
- **Svelte 5 runes**: https://svelte.dev/docs/svelte/what-are-runes, https://svelte.dev/docs/svelte/$state, https://svelte.dev/docs/svelte/$effect
- **Styling**: https://tailwindcss.com/docs/installation/using-vite, https://tailwindcss.com/docs/dark-mode, https://shadcn-svelte.com/docs/installation/vite
- **Rust SQLite**: https://docs.rs/rusqlite/latest/rusqlite/struct.Row.html
- **Fonts**: https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography

---

## Phase 1 — Scaffold the Tauri 2 + Svelte 5 project

**What to implement** — create a fresh Tauri 2 project at the repo root, replacing the Python source tree.

**Steps:**
1. **Decision locked: Option A.** Move the inner `Claude-to-Obsidian/Claude-to-Obsidian/` Python tree to `legacy-python/` (keep for reference), then scaffold the new project at the outer repo root. The nested inner `.git` directory is deleted — the outer repo becomes the single source of truth.
   - If the inner tree has uncommitted changes, stash or commit them first before moving.
2. Run `pnpm create tauri-app` (or `npm create tauri-app@latest` if pnpm not present). Answers:
   - Project name: `claude-to-obsidian`
   - Identifier: `com.cedrickgd.claude-to-obsidian`
   - Frontend language: **TypeScript / JavaScript**
   - Package manager: **pnpm**
   - UI template: **Svelte**
   - UI flavor: **TypeScript**
3. Verify the expected layout is produced (`src/`, `src-tauri/src/lib.rs`, `src-tauri/capabilities/default.json`, `tauri.conf.json`, `vite.config.ts`).
4. `pnpm install && pnpm tauri dev` — confirm the stock app window opens.
5. Install Tailwind v4 + shadcn-svelte:
   ```bash
   pnpm add -D tailwindcss @tailwindcss/vite
   pnpm dlx shadcn-svelte@latest init
   ```
   Add `tailwindcss()` plugin to `vite.config.ts`. Create `src/app.css` with `@import "tailwindcss";` and the dark-mode variant:
   ```css
   @import "tailwindcss";
   @custom-variant dark (&:where(.dark, .dark *));
   ```
   Import `src/app.css` in `src/main.ts`.
6. Install runtime dependencies (JS side):
   ```bash
   pnpm add @tauri-apps/api @tauri-apps/plugin-dialog @tauri-apps/plugin-store @tauri-apps/plugin-autostart @tauri-apps/plugin-opener @lucide/svelte
   ```
7. Install Rust dependencies — add to `src-tauri/Cargo.toml`:
   ```toml
   [dependencies]
   tauri = { version = "2", features = [] }
   tauri-plugin-dialog = "2"
   tauri-plugin-store = "2"
   tauri-plugin-autostart = "2"
   tauri-plugin-opener = "2"
   rusqlite = { version = "0.39", features = ["bundled"] }
   serde = { version = "1", features = ["derive"] }
   serde_json = "1"
   thiserror = "2"
   tokio = { version = "1", features = ["time", "rt", "macros", "sync"] }
   tracing = "0.1"
   tracing-subscriber = "0.3"
   chrono = { version = "0.4", features = ["serde"] }
   dirs = "5"  # for home directory detection
   ```
8. Wire plugins in `src-tauri/src/lib.rs`:
   ```rust
   pub fn run() {
       tauri::Builder::default()
           .plugin(tauri_plugin_dialog::init())
           .plugin(tauri_plugin_store::Builder::new().build())
           .plugin(tauri_plugin_opener::init())
           .plugin(tauri_plugin_autostart::init(
               tauri_plugin_autostart::MacosLauncher::LaunchAgent,
               Some(vec!["--minimized"]),
           ))
           .run(tauri::generate_context!())
           .expect("error while running tauri application");
   }
   ```
9. Add the base capability file at `src-tauri/capabilities/default.json` (see locked-in scope in next phases — start with `core:default`, `dialog:default`, `store:default`, `opener:allow-open-url`, `autostart:allow-enable`, `autostart:allow-disable`, `autostart:allow-is-enabled`).

**Verification checklist:**
- [ ] `pnpm tauri dev` opens a window titled "Claude to Obsidian" (will be stock template text — fine for this phase)
- [ ] `src-tauri/target/debug/` built without errors
- [ ] Tailwind classes work — add `<div class="p-4 bg-blue-500">test</div>` in `App.svelte`, see blue block
- [ ] Dark mode toggle works — manually add/remove `dark` class on `<html>` via devtools, Tailwind `dark:` variants react
- [ ] No deprecated-syntax warnings in Vite console

**Anti-pattern guards:**
- Don't add `svelte.config.js` with adapter-static — we're **not** using SvelteKit
- Don't commit `src-tauri/target/` or `node_modules/`
- Don't add `tailwind.config.js` — Tailwind v4 is CSS-first; configure via `@theme` blocks in `app.css`

---

## Phase 2 — Port the sync engine to Rust

**What to implement** — mirror the Python `sync.py` in Rust. Read observations + session_summaries from the user's `claude-mem.db`, write Markdown with YAML frontmatter to `<vault>/Claude Memories/{Observations,Summaries}/`, track incremental state in a JSON file.

**Module layout in `src-tauri/src/`:**
```
src-tauri/src/
├── main.rs          // existing thin shim
├── lib.rs           // Builder, plugin registration, command handlers
├── error.rs         // AppError enum + Serialize impl
├── config.rs        // Config struct, load/save via tauri-plugin-store
├── sync/
│   ├── mod.rs       // SyncEngine, run_once(), progress emit
│   ├── state.rs     // SyncState (last_observation_id, last_summary_id) + JSON persistence
│   ├── observations.rs
│   └── summaries.rs
└── autodetect.rs    // Claude DB + Obsidian vault discovery
```

**Reference the existing Python implementation** at `Claude-to-Obsidian/Claude-to-Obsidian/src/sync.py` (or `legacy-python/sync.py` if Phase 1 option A chosen). Copy the exact:
- Table names: `observations`, `session_summaries`
- Column names per table (see Python `SELECT *` columns accessed via dict lookup)
- Filename sanitizer regex: `[\\/*?:"<>|]` → `_`
- Filename pattern: `{project}_{id}_{title[:50]}.md` for observations, `{project}_Summary_{id}.md` for summaries
- YAML frontmatter structure (tags include `claude-memory`, the type, and lowercased project)
- Markdown body layout (sections: Narrative / Facts / Concepts for observations; Request / Investigated / Learned / Completed / Next Steps / Notes for summaries)

**Error type (copy into `error.rs`):**
```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error(transparent)] Io(#[from] std::io::Error),
    #[error(transparent)] Sqlite(#[from] rusqlite::Error),
    #[error(transparent)] Json(#[from] serde_json::Error),
    #[error("config: {0}")] Config(String),
    #[error("sync: {0}")]   Sync(String),
}
impl serde::Serialize for AppError {
    fn serialize<S: serde::Serializer>(&self, s: S) -> Result<S::Ok, S::Error> {
        s.serialize_str(&self.to_string())
    }
}
pub type AppResult<T> = Result<T, AppError>;
```

**Query pattern (use this shape — not `SELECT *` with dynamic columns):**
```rust
let conn = Connection::open_with_flags(&db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
let mut stmt = conn.prepare(
    "SELECT id, project, title, subtitle, type, created_at, narrative, facts, concepts, files_read, files_modified
     FROM observations WHERE id > ?1 ORDER BY id ASC"
)?;
let rows = stmt.query_map([last_id], |row| {
    Ok(ObservationRow {
        id:        row.get("id")?,
        project:   row.get::<_, Option<String>>("project")?,
        title:     row.get::<_, Option<String>>("title")?,
        // ...
        facts_raw: row.get::<_, Option<String>>("facts")?,
        concepts_raw: row.get::<_, Option<String>>("concepts")?,
    })
})?;
```
Parse `facts_raw` and `concepts_raw` with `serde_json::from_str::<Vec<String>>`. Handle `None` / empty string.

**Progress events** — emit from inside the loop so the UI can show "X of Y":
```rust
app.emit("sync:progress", serde_json::json!({
    "kind": "observation",
    "current": i + 1,
    "total": total
}))?;
```

**Command signatures to expose:**
```rust
#[tauri::command]
async fn run_sync(app: AppHandle, config: Config) -> AppResult<SyncReport> { ... }

#[tauri::command]
async fn probe_db(db_path: String) -> AppResult<DbStats> { ... }  // row counts, for UI preview
```

Register in `invoke_handler![run_sync, probe_db, ...]`. Wrap blocking DB work in `tauri::async_runtime::spawn_blocking`.

**Verification checklist:**
- [ ] `cargo test` in `src-tauri/` passes a unit test that creates an in-memory SQLite DB with two observations and verifies two `.md` files are produced
- [ ] Running `run_sync` from a hand-written JS test (add a temporary button in `App.svelte` that calls `invoke('run_sync', { config })`) produces files identical to the Python version (byte-compare against legacy output on the same DB)
- [ ] `sync:progress` events arrive in the JS console when listened
- [ ] Re-running sync on the same DB produces 0 new files (state persistence works)

**Anti-pattern guards:**
- Don't `SELECT *` and iterate by index — order is not guaranteed across SQLite versions. Name columns explicitly.
- Don't use `sqlx` macros — the DB is user-provided at runtime
- Don't add `tauri-plugin-sql` — wrong scope (it's for app-managed DBs under `AppConfig`)
- Don't do blocking SQLite calls directly in an async command — wrap with `spawn_blocking`
- Don't unwrap `row.get` on nullable columns — use `Option<T>`

---

## Phase 3 — Config persistence + auto-detect

**What to implement** — `Config` struct that persists via `tauri-plugin-store`, plus an auto-detect command that finds the Claude DB and Obsidian vault on Windows.

**Config shape:**
```rust
#[derive(Serialize, Deserialize, Clone, Debug, Default)]
pub struct Config {
    pub db_path: Option<PathBuf>,
    pub vault_path: Option<PathBuf>,
    pub interval_minutes: u32,       // default 15
    pub theme: Theme,                // Auto | Light | Dark
    pub autostart: bool,             // default false
    pub schedule_enabled: bool,      // default false
}
```

Store key namespace: `settings.json` via `tauri-plugin-store`. Commands:
```rust
#[tauri::command]
async fn load_config(app: AppHandle) -> AppResult<Config>

#[tauri::command]
async fn save_config(app: AppHandle, config: Config) -> AppResult<()>
```

**Auto-detect logic** — cross-platform via the `dirs` crate. One implementation, no platform forks:
- **Claude DB:** `dirs::home_dir()?.join(".claude-mem/claude-mem.db")` — same path on Windows and macOS.
- **Obsidian config:** `dirs::config_dir()?.join("obsidian/obsidian.json")` — resolves to:
  - Windows → `%APPDATA%\obsidian\obsidian.json`
  - macOS → `~/Library/Application Support/obsidian/obsidian.json`
  - Linux → `~/.config/obsidian/obsidian.json` (dev only)
- Parse the JSON, walk `vaults.<id>.path`, return the most-recently-opened vault (maximize by `ts` field if present, otherwise first entry).

```rust
#[tauri::command]
async fn auto_detect() -> AppResult<AutoDetectResult> {
    let db = dirs::home_dir()
        .map(|h| h.join(".claude-mem").join("claude-mem.db"))
        .filter(|p| p.exists());

    let obsidian_cfg = dirs::config_dir()
        .map(|c| c.join("obsidian").join("obsidian.json"))
        .filter(|p| p.exists());

    let vault = obsidian_cfg.and_then(|p| find_first_obsidian_vault(&p).ok());
    Ok(AutoDetectResult { db_path: db, vault_path: vault })
}
```

**Verification checklist:**
- [ ] Set a value via `save_config`, restart app, `load_config` returns the same value
- [ ] Config file lives at Tauri's app config dir (`%APPDATA%/com.cedrickgd.claude-to-obsidian/settings.json`)
- [ ] `auto_detect` returns both paths on a machine that has claude-mem and Obsidian installed

**Anti-pattern guards:**
- Don't hardcode `%APPDATA%` — use the `dirs` crate so the same code works on mac/Linux
- Don't write config with `std::fs::write` — use `tauri-plugin-store` so JS and Rust share one source of truth
- Don't panic on malformed `obsidian.json` — return `Ok(None)` and let the UI prompt manual selection

---

## Phase 4 — Svelte UI: the beautiful part

**What to implement** — single-page UI that replaces the Tkinter layout with a Fluent-adjacent design. Ship-ready components: header with theme toggle, two path cards with inline browse buttons, settings card (interval + automation toggles), action row, live progress area, status footer.

### 4.1 Visual design spec

Layout (single scrollable column, max-width ~640px, centered):
```
┌─────────────────────────────────────────────┐
│  Claude → Obsidian               [☀/🌙/🖥]  │  ← 28/36 semibold title + theme mode picker
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐   │
│  │ 📀 Claude Memory Database            │   │  ← card with icon, label, path preview
│  │ /Users/.../claude-mem.db   [Browse]  │   │
│  │ ✓ 1,234 observations · 42 summaries   │  │  ← live stats after probe_db
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │ 📁 Obsidian Vault                    │   │
│  │ /Users/.../MyVault         [Browse]  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Sync Settings                              │  ← 14/20 semibold section header
│  ┌──────────────────────────────────────┐   │
│  │  Interval: [  15  ] minutes          │   │
│  │  ☐ Run sync in background            │   │
│  │  ☐ Launch at login                   │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  [Preview]  [Sync Now]  [Open in Obsidian]  │
│  [Apply & Automate]  ←primary, full-width   │
│                                             │
│  ◐ Syncing observations… 47 / 230  ━━━━──   │  ← progress only when active
├─────────────────────────────────────────────┤
│ ✓ Last sync: 2 min ago · 12 new files       │  ← status footer (see Phase 5.6)
└─────────────────────────────────────────────┘

Plus: **first-run experience** shown instead of this layout when `!config.dbPath || !config.vaultPath` — see Phase 5.1 for the onboarding wizard.
```

Tokens (declare in `app.css` via `@theme`):
- Surface tokens: `--color-surface` (bg), `--color-surface-elevated` (card), `--color-border`, `--color-accent` (Windows-ish blue `#0078d4`)
- Typography: use the Fluent type ramp — `text-xs` → `caption`, `text-sm` → `body`, `text-xl` → `subtitle`, `text-3xl font-semibold` → `title`
- Spacing: 16px base, cards `p-5`, section gaps `space-y-4`
- Corners: `rounded-xl` on cards, `rounded-lg` on inputs/buttons (Win11 ~8px)
- Shadows: subtle — `shadow-sm` on cards in light mode, none in dark (elevation via `bg-white/5`)
- Motion: `transition-colors duration-150` on all interactive elements

### 4.2 Component inventory (shadcn-svelte add)

```bash
pnpm dlx shadcn-svelte@latest add button input label checkbox progress separator
```

Then hand-write thin wrappers:
- `src/lib/components/PathCard.svelte` — label + readonly input + browse button + optional stats line
- `src/lib/components/SettingsCard.svelte` — composes Input + Checkbox rows
- `src/lib/components/ThemeToggle.svelte` — cycles Auto → Light → Dark using Lucide `Sun/Moon/Monitor`
- `src/lib/components/SyncProgress.svelte` — listens to `sync:progress`, shows Progress bar + text
- `src/lib/components/OpenInObsidian.svelte` — action button with deep-link + file-manager fallback (defined in Phase 5.4)
- `src/lib/components/LastSyncStatus.svelte` — footer line with relative timestamp (Phase 5.6)

Deferred to Phase 5 (not needed for the main screen yet):
- `src/lib/components/Onboarding.svelte` + 5 step panels
- `src/lib/components/CreateVaultDialog.svelte`

### 4.3 State organization

Create `src/lib/stores/config.svelte.ts` — exports a singleton `$state` object and load/save helpers:
```ts
import { invoke } from '@tauri-apps/api/core';

export const config = $state({
  dbPath: '', vaultPath: '', intervalMinutes: 15,
  theme: 'auto' as 'auto' | 'light' | 'dark',
  autostart: false, scheduleEnabled: false,
});

export async function loadConfig() {
  const loaded = await invoke<Config>('load_config');
  Object.assign(config, loaded);
}
// Debounced autosave pattern wired in App.svelte via $effect
```

Important: **shared state across `.svelte` files must be exported from a `.svelte.ts` module** (runes require the compiler to see the file). Don't put it in a `.ts` file.

### 4.4 Theme implementation

1. On boot read `config.theme`. If `"auto"`, call `getCurrentWindow().theme()` and listen to `onThemeChanged`. If `"dark"`/`"light"`, pin with `setTheme(...)`.
2. Toggle the `dark` class on `document.documentElement` to match — Tailwind `dark:` variants respond.
3. Inline script in `index.html` `<head>` to avoid FOUC:
   ```html
   <script>
     const stored = localStorage.getItem('theme');
     const dark = stored === 'dark' || (stored !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
     document.documentElement.classList.toggle('dark', dark);
   </script>
   ```

### 4.5 Debounced autosave wiring (in `App.svelte`)

```svelte
<script lang="ts">
  import { config } from '$lib/stores/config.svelte';
  import { invoke } from '@tauri-apps/api/core';

  let timer: ReturnType<typeof setTimeout>;
  $effect(() => {
    const snap = $state.snapshot(config);  // read tracks every prop → effect re-fires on change
    clearTimeout(timer);
    timer = setTimeout(() => invoke('save_config', { config: snap }), 400);
    return () => clearTimeout(timer);
  });
</script>
```

**Verification checklist:**
- [ ] All three theme modes work: Auto follows OS preference, manual Light/Dark pins
- [ ] No FOUC on cold start (dark users don't see a white flash)
- [ ] Editing interval quickly doesn't fire save on every keystroke (check with `tracing` logs in Rust)
- [ ] Path cards show stats after `probe_db` runs
- [ ] Sync progress bar fills and text updates live during a sync
- [ ] Resize window to 400×300 — layout doesn't break (responsive)
- [ ] All Lucide icons render; no missing-icon squares
- [ ] Fonts look crisp on a Windows 11 machine (Segoe UI Variable loaded)

**Anti-pattern guards:**
- Don't use `on:click` — Svelte 5 uses `onclick={}`
- Don't use `export let foo` — use `let { foo } = $props()`
- Don't destructure `config` in components — breaks reactivity; pass the whole object or access `config.foo` directly
- Don't write `$: value = config.path` — use `let value = $derived(config.path)`
- Don't put shared runes state in `.ts` files — the compiler only processes `.svelte.ts` / `.svelte`
- Don't send raw `$state` proxies over `invoke` — wrap in `$state.snapshot(...)`

---

## Phase 5 — Onboarding wizard + create-vault flow

**What to implement** — a first-run wizard that guides a new user from zero config to a working sync in under a minute, plus an always-available "Create new vault" action and "Open in Obsidian" button.

### 5.1 Onboarding trigger + state machine

Boot-time check in `App.svelte`:
```ts
import { config } from '$lib/stores/config.svelte';
let needsOnboarding = $derived(!config.dbPath || !config.vaultPath);
```

If `needsOnboarding` is true, render `<Onboarding />` instead of the main settings screen.

**Five steps** (progress dots at the top of the dialog, `←` back / `→` continue):
1. **Welcome** — Title: "Sync your Claude memories into Obsidian." Subtitle: "We'll help you get set up in a minute." [Get started]
2. **Find Claude memories** — Runs `invoke('auto_detect')` on mount. If `db_path` returned: "We found your Claude memories. [Use this] / [Choose a different file]". If not found: "We couldn't find them automatically. [Browse...]"
3. **Choose your vault** — Three large cards:
   - Auto-detected vault (if present) — [Use this vault]
   - [Browse existing vault] → `open({ directory: true })`
   - [Create new vault] → opens `<CreateVaultDialog>` (see 5.3)
4. **Preview** — Runs `invoke('probe_sync', { dbPath, state: defaultState })`. Shows: "We'll sync **15 observations** and **3 summaries** on first run." [Looks good]
5. **Automation** — Two checkboxes: "Run sync in background every [15] minutes" and "Launch at login". [Finish] sets `config.schedule_enabled` / `config.autostart` and drops the user on the main screen.

The main screen always has "Run first-time setup again…" in an overflow menu to re-enter the wizard.

### 5.2 Create-vault command (Rust)

```rust
// src-tauri/src/vault.rs
use std::path::{Path, PathBuf};

const WELCOME_MD: &str = r#"---
tags: [claude-memory, welcome]
---
# Welcome to your Claude memory vault

Your Claude Code observations and session summaries will be synced into `Claude Memories/`.

- `Observations/` — specific facts and findings from sessions
- `Summaries/` — high-level recaps of what each session accomplished

Open this folder in Obsidian to start browsing your knowledge graph.
"#;

#[tauri::command]
pub async fn create_vault(parent_dir: String, vault_name: String) -> AppResult<PathBuf> {
    let parent = PathBuf::from(&parent_dir);
    if !parent.is_dir() {
        return Err(AppError::Config(format!("Parent directory does not exist: {parent_dir}")));
    }
    let clean_name = sanitize_folder_name(&vault_name);
    if clean_name.is_empty() {
        return Err(AppError::Config("Vault name cannot be empty".into()));
    }
    let vault = parent.join(&clean_name);
    if vault.exists() {
        return Err(AppError::Config(format!("A folder already exists at: {}", vault.display())));
    }

    // .obsidian/ makes the folder a recognizable Obsidian vault
    std::fs::create_dir_all(vault.join(".obsidian"))?;
    std::fs::create_dir_all(vault.join("Claude Memories").join("Observations"))?;
    std::fs::create_dir_all(vault.join("Claude Memories").join("Summaries"))?;
    std::fs::write(vault.join("Welcome.md"), WELCOME_MD)?;
    Ok(vault)
}

fn sanitize_folder_name(s: &str) -> String {
    s.chars().filter(|c| !r#"\/:*?"<>|"#.contains(*c)).collect::<String>().trim().to_string()
}
```

Register in `invoke_handler![...]`.

### 5.3 `CreateVaultDialog.svelte`

```svelte
<script lang="ts">
  import { open } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';

  let { onCreated, onCancel }: { onCreated: (path: string) => void; onCancel: () => void } = $props();
  let parentDir = $state('');
  let vaultName = $state('Claude Memories');
  let error = $state<string | null>(null);
  let busy = $state(false);

  async function pickParent() {
    const path = await open({ directory: true, title: 'Choose where to create the vault' });
    if (path) parentDir = path as string;
  }

  async function create() {
    busy = true; error = null;
    try {
      const vault = await invoke<string>('create_vault', { parentDir, vaultName });
      onCreated(vault);
    } catch (e) { error = String(e); } finally { busy = false; }
  }

  let canCreate = $derived(parentDir.length > 0 && vaultName.trim().length > 0 && !busy);
</script>

<div class="space-y-4">
  <div>
    <label class="text-sm font-medium">Location</label>
    <div class="flex gap-2 mt-1">
      <Input bind:value={parentDir} placeholder="Pick a parent folder…" readonly />
      <Button variant="outline" onclick={pickParent}>Browse</Button>
    </div>
  </div>
  <div>
    <label class="text-sm font-medium">Vault name</label>
    <Input bind:value={vaultName} class="mt-1" />
  </div>
  {#if error}<p class="text-sm text-red-500">{error}</p>{/if}
  <div class="flex justify-end gap-2">
    <Button variant="ghost" onclick={onCancel}>Cancel</Button>
    <Button onclick={create} disabled={!canCreate}>Create vault</Button>
  </div>
</div>
```

### 5.4 "Open in Obsidian" action

Uses `tauri-plugin-opener` (already installed in Phase 1). Capability scope in `default.json`:
```json
{ "identifier": "opener:allow-open-url", "allow": [{ "url": "obsidian://*" }, { "url": "file://*" }] }
```

Svelte wrapper:
```svelte
<script lang="ts">
  import { openUrl } from '@tauri-apps/plugin-opener';
  import { ExternalLink } from '@lucide/svelte';
  import { config } from '$lib/stores/config.svelte';

  async function openInObsidian() {
    const path = encodeURIComponent(config.vaultPath);
    try {
      await openUrl(`obsidian://open?path=${path}`);
    } catch {
      // Obsidian not installed or protocol unhandled — open in file manager
      await openUrl(`file://${config.vaultPath}`);
    }
  }
</script>
<Button variant="outline" onclick={openInObsidian}>
  <ExternalLink size={14} /> Open in Obsidian
</Button>
```

### 5.5 Dry-run preview command

```rust
#[derive(Serialize)]
pub struct SyncPreview { pub new_observations: i64, pub new_summaries: i64 }

#[tauri::command]
pub async fn probe_sync(db_path: String, state: SyncState) -> AppResult<SyncPreview> {
    tauri::async_runtime::spawn_blocking(move || {
        let conn = Connection::open_with_flags(&db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
        let n_obs: i64 = conn.query_row(
            "SELECT COUNT(*) FROM observations WHERE id > ?1",
            [state.last_observation_id], |r| r.get(0))?;
        let n_sum: i64 = conn.query_row(
            "SELECT COUNT(*) FROM session_summaries WHERE id > ?1",
            [state.last_summary_id], |r| r.get(0))?;
        Ok(SyncPreview { new_observations: n_obs, new_summaries: n_sum })
    }).await.map_err(|e| AppError::Sync(e.to_string()))?
}
```

Used by step 4 of onboarding and as a "Preview" button next to "Sync Now" on the main screen.

### 5.6 Last-sync status + timestamp

Extend `SyncState`:
```rust
pub struct SyncState {
    pub last_observation_id: i64,
    pub last_summary_id: i64,
    pub last_run_at: Option<DateTime<Utc>>,
    pub last_run_report: Option<SyncReport>,
}
```

Footer renders either "No syncs yet" or, using `chrono::Local::now().signed_duration_since(last_run_at)` formatted as "3 min ago" / "1 hour ago" / "2 days ago":
```
✓ Last sync 3 min ago · 12 new files
```

**Verification checklist:**
- [ ] Clear `%APPDATA%/com.cedrickgd.claude-to-obsidian/` (and `~/Library/Application Support/...` on mac) → onboarding wizard appears on next launch
- [ ] Complete the wizard with auto-detect path → main screen shows populated paths
- [ ] Create vault: folder exists with `.obsidian/`, `Claude Memories/{Observations,Summaries}/`, `Welcome.md`
- [ ] Open in Obsidian with Obsidian installed → Obsidian launches with the chosen vault
- [ ] Open in Obsidian without Obsidian installed → system file manager opens the folder
- [ ] Probe sync shows correct counts on a real `claude-mem.db`; running it does not write files
- [ ] Status footer updates timestamp after each successful sync
- [ ] Re-entering onboarding from the overflow menu does not lose already-saved config unless the user completes the wizard

**Anti-pattern guards:**
- Don't pop the onboarding wizard every launch — only when `db_path` or `vault_path` is empty
- Don't create the vault at a non-existent parent path — return a clear error and let the UI prompt [Browse]
- Don't write a `README.md` into the user's vault; `Welcome.md` is enough and the user can delete it
- Don't fail silently when `obsidian://` is unhandled — always catch and fall back to file-manager
- Don't forget `spawn_blocking` around SQLite queries in `probe_sync` — even the `COUNT(*)` is blocking

---

## Phase 6 — Automation: in-process scheduler + autostart

**What to implement** — a background Tokio task that runs `run_sync` on an interval when `config.schedule_enabled` is true, plus `tauri-plugin-autostart` wired to the "Launch at login" checkbox.

### 5.1 Background sync task

In `lib.rs`'s `setup` hook, spawn a cancellable task:
```rust
use tokio_util::sync::CancellationToken;   // cargo add tokio-util

.setup(|app| {
    let handle = app.handle().clone();
    let token = CancellationToken::new();
    app.manage(SchedulerHandle { token: token.clone() });

    tauri::async_runtime::spawn(async move {
        loop {
            // Read config each tick so interval changes take effect without restart
            let cfg = crate::config::load(&handle).await.unwrap_or_default();
            if !cfg.schedule_enabled {
                tokio::select! {
                    _ = tokio::time::sleep(std::time::Duration::from_secs(30)) => continue,
                    _ = token.cancelled() => break,
                }
            }
            let dur = std::time::Duration::from_secs((cfg.interval_minutes as u64).max(1) * 60);
            tokio::select! {
                _ = tokio::time::sleep(dur) => {
                    if let Err(e) = crate::sync::run_once(&handle, &cfg).await {
                        tracing::warn!("scheduled sync failed: {e:?}");
                    }
                }
                _ = token.cancelled() => break,
            }
        }
    });
    Ok(())
})
```

Cancel on app exit in the `RunEvent::ExitRequested` hook — prevents the task from outliving the window.

### 5.2 Autostart wiring

Add plugin capability in `src-tauri/capabilities/default.json`:
```json
"permissions": [
  "autostart:allow-enable",
  "autostart:allow-disable",
  "autostart:allow-is-enabled"
]
```

Svelte checkbox handler (in `SettingsCard.svelte`):
```ts
import { enable, disable, isEnabled } from '@tauri-apps/plugin-autostart';
async function onToggle(v: boolean) {
  v ? await enable() : await disable();
  config.autostart = await isEnabled();  // read back to stay truthful
}
```

Initial sync on boot — in `App.svelte`'s top-level `$effect`, call `isEnabled()` once to reconcile `config.autostart` with OS reality.

### 5.3 Intentional non-goals

- **No `schtasks.exe` shell-out.** Skipped: UAC surface, Windows-only, duplicates in-process scheduler.
- **No `planif` crate.** Skipped: archived 2024-07.
- **No `notify` file-watching for v1.** Skipped: `claude-mem.db-wal` noise complicates debouncing; 15-min poll is sufficient.

All three can be revisited post-v1 if users complain.

**Verification checklist:**
- [ ] Enable schedule → wait one interval → observe new files in vault
- [ ] Change interval from 15 → 5 while running → next tick respects the new value (no restart needed)
- [ ] Close app → reopen → task cancellation fired cleanly (no stale file locks)
- [ ] Enable "Launch at login" → restart Windows → app auto-launches minimized
- [ ] Disable "Launch at login" → restart Windows → app does not launch

**Anti-pattern guards:**
- Don't spawn the interval task with `tokio::spawn` — use `tauri::async_runtime::spawn` (same thing today but survives future runtime swaps)
- Don't hold a `tauri::State` lock across an `await` — deadlock risk
- Don't forget to cancel on exit — the task will keep the process alive on some platforms

---

## Phase 7 — Polish: logo, icons, window config, mac + Windows bundling

**What to implement** — logo, icon set, production window config, Windows + macOS bundles.

### 7.1 Logo proposal

**Concept: "Crystallized memory."** An abstract hexagonal gem (nodding to Obsidian's crystalline aesthetic) with a small orange spark entering the top face (nodding to Claude's orange accent without copying either company's trademark). Reads clearly at 16×16 (just the hex silhouette + spark), gains facet detail at 128×128+.

Colors:
- Purple gradient `#8b6ab8 → #4a2d7f` (crystal body)
- Accent `#ff9500` (spark / entry point)
- Stroke `#2d1a4f` (outer contour for contrast on light backgrounds)

Save the following as `src-tauri/icons/source.svg`, then rasterize to a 1024×1024 PNG (`rsvg-convert` / Inkscape CLI / `resvg`) before running `pnpm tauri icon`:

```svg
<svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="body" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#8b6ab8"/>
      <stop offset="1" stop-color="#4a2d7f"/>
    </linearGradient>
  </defs>
  <!-- Hex crystal body -->
  <path d="M128 24 L220 76 L220 180 L128 232 L36 180 L36 76 Z"
        fill="url(#body)" stroke="#2d1a4f" stroke-width="4" stroke-linejoin="round"/>
  <!-- Facet lines: top vertex to left/right/center-bottom -->
  <path d="M128 24 L128 128 M36 76 L128 128 M220 76 L128 128 M128 128 L128 232"
        stroke="#c8a8e8" stroke-width="1.5" fill="none" opacity="0.4"/>
  <!-- Orange spark entering the top face -->
  <path d="M128 40 L142 62 L128 84 L114 62 Z" fill="#ff9500"/>
  <!-- Subtle highlight -->
  <path d="M36 76 L128 24 L128 128 Z" fill="white" opacity="0.08"/>
</svg>
```

**Alternates** (if the hex doesn't land — swap the SVG and re-run `tauri icon`):
- Minimalist "C→O" monogram in geometric sans
- Two overlapping discs (orange + purple) with an arrow motif in the overlap
- Infinity loop split across the two brand colors

Deliverable for Phase 7: source SVG in the repo, generated PNG/ICO/ICNS in `src-tauri/icons/` (gitignored except the source).

### 7.2 Icon generation (both platforms in one command)

```bash
# Rasterize the SVG once
resvg src-tauri/icons/source.svg src-tauri/icons/source.png -w 1024 -h 1024
# Or: inkscape --export-type=png --export-width=1024 src-tauri/icons/source.svg

# Tauri generates every required size/format:
pnpm tauri icon src-tauri/icons/source.png
# → icon.ico (Windows) · icon.icns (macOS) · multiple PNGs
```

### 7.3 Window config — `tauri.conf.json`

```json
{
  "app": {
    "windows": [{
      "label": "main",
      "title": "Claude to Obsidian",
      "width": 720, "height": 720,
      "minWidth": 480, "minHeight": 540,
      "resizable": true,
      "decorations": true,
      "theme": null,
      "titleBarStyle": "Visible"
    }]
  },
  "bundle": {
    "active": true,
    "targets": ["msi", "nsis", "app", "dmg"],
    "icon": ["icons/32x32.png", "icons/128x128.png", "icons/icon.ico", "icons/icon.icns"],
    "identifier": "com.cedrickgd.claude-to-obsidian",
    "category": "Productivity",
    "shortDescription": "Sync Claude memories into Obsidian",
    "longDescription": "A native desktop sync tool that exports your Claude Code observations and session summaries as Markdown into an Obsidian vault.",
    "macOS": {
      "minimumSystemVersion": "11.0",
      "exceptionDomain": ""
    }
  }
}
```

`titleBarStyle: "Visible"` keeps the native OS title bar on both platforms. On macOS this gives the standard traffic-light controls; `theme: null` means immersive dark-mode title bar on Windows 11 and automatic dark appearance on macOS.

### 7.4 Build

**Windows** (from a Windows machine):
```bash
pnpm tauri build
# → src-tauri/target/release/bundle/msi/*.msi
# → src-tauri/target/release/bundle/nsis/*.exe
```

**macOS** (from a mac):
```bash
pnpm tauri build
# → src-tauri/target/release/bundle/macos/*.app
# → src-tauri/target/release/bundle/dmg/*.dmg
```
Unsigned mac builds: when running, users must right-click the `.app` and choose "Open" once to bypass Gatekeeper (documented in README). Code signing is deferred past v1 (per user decision).

**Cross-compile note:** Tauri does not cross-compile macOS from Windows reliably — each platform builds its own bundle. A GitHub Actions matrix (`windows-latest`, `macos-latest`) handles both in CI. Add a `.github/workflows/release.yml` that runs `pnpm tauri build` on both runners and uploads bundles to a release. (CI file is a nice-to-have; ship manually from each machine first.)

### 7.5 Smoke test both installers

- Windows: install MSI → launch from Start menu → complete onboarding → run sync
- macOS: open DMG → drag app to `/Applications` → launch → complete onboarding → run sync
- Uninstall: MSI provides one; mac is just "drag to trash" plus clearing `~/Library/Application Support/com.cedrickgd.claude-to-obsidian/`

**Verification checklist:**
- [ ] App icon shows in Windows Start menu + taskbar + title bar
- [ ] App icon shows in macOS Dock + Finder + Launchpad
- [ ] MSI installer runs without admin prompt (Tauri default)
- [ ] macOS `.app` runs after first Gatekeeper bypass
- [ ] Title bar follows OS theme on both platforms
- [ ] `pnpm tauri build` output is under ~15 MB per platform (typical Tauri size; may be larger with mac universal binary)
- [ ] Logo SVG renders cleanly at 16×16 and 1024×1024

**Anti-pattern guards:**
- Don't commit generated icons except the source SVG + source PNG
- Don't bundle Segoe UI Variable — Microsoft EULA forbids redistribution (Windows-only system font; use the fallback chain)
- Don't sign with an ad-hoc identity on mac — unsigned is fine for v1; signed-but-unnotarized is worse UX than unsigned (triggers a different scary dialog)
- Don't ship `.deb`/`.AppImage` for Linux in v1 — code works but we haven't agreed to support that platform

---

## Phase 8 — Verification sweep

Final pass before calling it done.

**Documentation checks:**
- [ ] Grep for `@tauri-apps/api/tauri` — should be zero hits (v1 path)
- [ ] Grep for `on:click|on:change|on:input` — should be zero hits (Svelte 4 syntax)
- [ ] Grep for `export let ` in `.svelte` files — should be zero hits
- [ ] Grep for `\$:` reactive declarations — should be zero hits
- [ ] Grep for `allowlist` in `tauri.conf.json` — should be zero hits (v1 API)

**Functional checks:**
- [ ] Run sync against the same `claude-mem.db` with the Python tool and the Rust tool. Diff the produced `.md` files. Frontmatter must match; body must match modulo whitespace.
- [ ] Verify capability scope — try reading a file outside the granted scopes from JS, should fail cleanly
- [ ] Verify error messages surface to the UI with readable text (not `[object Object]`)
- [ ] Onboarding flow completes end-to-end with a newly created vault
- [ ] "Open in Obsidian" works on a machine with Obsidian installed; falls back to file manager on one without

**UX checks:**
- [ ] Cold start to first interactive frame: < 2 seconds
- [ ] Manual sync of 1000 observations: progress bar visibly moves; UI stays responsive
- [ ] Theme switch: no flash, no layout shift
- [ ] Window resize: content reflows gracefully
- [ ] All checks performed on both Windows 11 and macOS (12+)

**Packaging checks:**
- [ ] MSI + NSIS installers both install/uninstall cleanly (Windows)
- [ ] DMG mounts and app drags to `/Applications`; launches after first Gatekeeper bypass (macOS)
- [ ] Autostart registry entry cleaned up on uninstall (Windows: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- [ ] Autostart LaunchAgent cleaned up on uninstall (macOS: `~/Library/LaunchAgents/com.cedrickgd.claude-to-obsidian.plist`)
- [ ] Config directory is the expected one per platform: `%APPDATA%\com.cedrickgd.claude-to-obsidian\` on Windows, `~/Library/Application Support/com.cedrickgd.claude-to-obsidian/` on macOS

---

## Dependency summary

**Rust (`src-tauri/Cargo.toml`):**
```toml
tauri = "2"
tauri-plugin-dialog = "2"
tauri-plugin-store = "2"
tauri-plugin-autostart = "2"
tauri-plugin-opener = "2"
rusqlite = { version = "0.39", features = ["bundled"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tokio = { version = "1", features = ["time", "rt", "macros", "sync"] }
tokio-util = "0.7"
tracing = "0.1"
tracing-subscriber = "0.3"
chrono = { version = "0.4", features = ["serde"] }
dirs = "5"
```

**JS (`package.json`):**
```json
{
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/plugin-dialog": "^2.0.0",
    "@tauri-apps/plugin-store": "^2.0.0",
    "@tauri-apps/plugin-autostart": "^2.0.0",
    "@tauri-apps/plugin-opener": "^2.0.0",
    "@lucide/svelte": "^0.400.0",
    "svelte": "^5.0.0"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^5.0.0",
    "@tauri-apps/cli": "^2.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.5.0",
    "vite": "^5.0.0"
  }
}
```

---

## Decisions locked in (2026-04-19)

| # | Question | Answer |
|---|---|---|
| 1 | Phase 1 scaffold location | **A** — archive Python to `legacy-python/`, scaffold new project at repo root |
| 2 | Platforms | **Windows + macOS** (Linux code-compatible but no bundle) |
| 3 | Logo | **Proposed in Phase 7.1** — crystalline hexagonal gem, purple gradient with orange spark |
| 4 | Code signing | **Deferred past v1** — unsigned builds; users do one-time Gatekeeper bypass on mac |

## How to execute this plan

Each phase is self-contained: its own doc references, code snippets, verification checklist, and anti-pattern guards. To run a phase in a fresh session:

```
/claude-mem:do
# When prompted, point at this REWRITE_PLAN.md and specify which phase to execute.
```

Phases are numbered to indicate dependencies — execute them in order. Within a single long session you can chain multiple phases, but starting fresh per phase keeps context clean and makes the verification steps easier to trust.

**Phase map at a glance:**
1. Scaffold Tauri 2 + Svelte 5 project, archive Python, install all deps
2. Port sync engine to Rust (rusqlite, markdown writer, state persistence)
3. Config + auto-detect (cross-platform via `dirs` crate)
4. Core Svelte UI (layout, theming, components)
5. Onboarding wizard + create-vault + open-in-Obsidian + dry-run + last-sync status
6. Background scheduler + autostart
7. Logo, icons, window config, Windows + macOS bundling
8. Verification sweep
