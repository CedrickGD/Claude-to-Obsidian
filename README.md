# Claude to Obsidian Memory Sync

A lightweight tool to automatically export your Claude Desktop memory plugin observations and summaries into your Obsidian Vault as Markdown files.

## Features
- **Automatic Sync:** Set up a Windows Scheduled Task with one click.
- **Project Organization:** Memories are grouped by project name.
- **YAML Metadata:** Full frontmatter for easy filtering in Obsidian.
- **Incremental:** Only syncs new entries since the last run.
- **GUI:** Simple interface for configuration and manual triggers.

## Prerequisites
- Windows OS (for the automated task)
- Python 3.x
- [Claude Memory Plugin](https://github.com/anthropics/claude-mem) installed and active.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/CedrickGD/claude-to-obsidian.git
   cd claude-to-obsidian
   ```
2. Run the application:
   ```bash
   python src/main.py
   ```

## Setup
1. **Auto-Detect:** Click the "Auto-Detect Obsidian" button to let the app find your Claude database and your primary Obsidian vault.
2. **Manual Paths:** If detection fails, browse to your `claude-mem.db` (usually in `~/.claude-mem/`) and your Obsidian Vault folder.
3. **Save & Sync:** Click "Save Config" then "Run Sync Now" to verify everything is working.
4. **Automate:** Click "Setup Scheduled Task" to have your memories automatically synced every 10 minutes in the background.

## File Structure in Obsidian
Your memories will appear in a folder named `Claude Memories` inside your vault:
- `/Claude Memories/Observations/` - Specific facts and findings.
- `/Claude Memories/Summaries/` - High-level session summaries.

## License
MIT
