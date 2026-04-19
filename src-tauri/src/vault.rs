use std::path::{Path, PathBuf};

use crate::error::{AppError, AppResult};

const WELCOME_MD: &str = r#"---
tags: [claude-memory, welcome]
---
# Welcome to your Claude memory vault

Your Claude Code observations and session summaries will be synced into `Claude Memories/`.

- `Observations/` — specific facts and findings from sessions
- `Summaries/` — high-level recaps of what each session accomplished

Open this folder in Obsidian to start browsing your knowledge graph.
"#;

pub fn create(parent_dir: &Path, vault_name: &str) -> AppResult<PathBuf> {
    if !parent_dir.is_dir() {
        return Err(AppError::Config(format!(
            "Parent directory does not exist: {}",
            parent_dir.display()
        )));
    }
    let clean_name: String = vault_name
        .chars()
        .filter(|c| !r#"\/:*?"<>|"#.contains(*c))
        .collect::<String>()
        .trim()
        .to_string();
    if clean_name.is_empty() {
        return Err(AppError::Config("Vault name cannot be empty".into()));
    }

    let vault = parent_dir.join(&clean_name);
    if vault.exists() {
        return Err(AppError::Config(format!(
            "A folder already exists at: {}",
            vault.display()
        )));
    }

    std::fs::create_dir_all(vault.join(".obsidian"))?;
    std::fs::create_dir_all(vault.join("Claude Memories").join("Observations"))?;
    std::fs::create_dir_all(vault.join("Claude Memories").join("Summaries"))?;
    std::fs::write(vault.join("Welcome.md"), WELCOME_MD)?;
    Ok(vault)
}
