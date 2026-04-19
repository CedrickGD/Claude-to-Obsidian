use std::path::{Path, PathBuf};

use serde::Serialize;

use crate::error::{AppError, AppResult};

#[derive(Serialize, Default, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct AutoDetectResult {
    pub db_path: Option<PathBuf>,
    pub vault_path: Option<PathBuf>,
}

pub fn detect() -> AutoDetectResult {
    let db_path = dirs::home_dir()
        .map(|h| h.join(".claude-mem").join("claude-mem.db"))
        .filter(|p| p.exists());

    let vault_path = dirs::config_dir()
        .map(|c| c.join("obsidian").join("obsidian.json"))
        .filter(|p| p.exists())
        .and_then(|p| find_first_obsidian_vault(&p).ok());

    AutoDetectResult {
        db_path,
        vault_path,
    }
}

fn find_first_obsidian_vault(config_path: &Path) -> AppResult<PathBuf> {
    let text = std::fs::read_to_string(config_path)?;
    let value: serde_json::Value = serde_json::from_str(&text)?;
    let vaults = value
        .get("vaults")
        .and_then(|v| v.as_object())
        .ok_or_else(|| AppError::Config("no vaults in obsidian.json".into()))?;

    // Pick most-recently-opened by `ts`, fallback to first entry
    let best = vaults
        .values()
        .filter_map(|v| {
            let path = v.get("path")?.as_str()?;
            let ts = v.get("ts").and_then(|t| t.as_i64()).unwrap_or(0);
            let exists = Path::new(path).exists();
            Some((exists, ts, PathBuf::from(path)))
        })
        .max_by_key(|(exists, ts, _)| (*exists, *ts))
        .map(|(_, _, p)| p)
        .ok_or_else(|| AppError::Config("no vault entries found".into()))?;
    Ok(best)
}
