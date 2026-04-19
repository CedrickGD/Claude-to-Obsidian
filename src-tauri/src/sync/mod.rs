pub mod observations;
pub mod summaries;

use std::path::{Path, PathBuf};

use chrono::{DateTime, Utc};
use rusqlite::{Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter};

use crate::error::{AppError, AppResult};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SyncState {
    pub last_observation_id: i64,
    pub last_summary_id: i64,
    pub last_run_at: Option<DateTime<Utc>>,
    pub last_run_report: Option<SyncReport>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncReport {
    pub observations_written: u32,
    pub summaries_written: u32,
    pub duration_ms: u128,
}

#[derive(Debug, Clone, Copy, Serialize)]
pub struct SyncPreview {
    pub new_observations: i64,
    pub new_summaries: i64,
}

#[derive(Serialize, Clone)]
pub struct SyncProgress {
    pub kind: &'static str,
    pub current: u32,
    pub total: u32,
}

impl SyncState {
    pub fn load(path: &Path) -> AppResult<Self> {
        if !path.exists() {
            return Ok(Self::default());
        }
        let text = std::fs::read_to_string(path)?;
        Ok(serde_json::from_str(&text)?)
    }

    pub fn save(&self, path: &Path) -> AppResult<()> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let text = serde_json::to_string_pretty(self)?;
        std::fs::write(path, text)?;
        Ok(())
    }
}

pub fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| if r#"\/*?:"<>|"#.contains(c) { '_' } else { c })
        .collect()
}

pub fn ensure_vault_dirs(vault_path: &Path) -> AppResult<(PathBuf, PathBuf)> {
    let obs_dir = vault_path.join("Claude Memories").join("Observations");
    let sum_dir = vault_path.join("Claude Memories").join("Summaries");
    std::fs::create_dir_all(&obs_dir)?;
    std::fs::create_dir_all(&sum_dir)?;
    Ok((obs_dir, sum_dir))
}

pub fn run_once(
    app: &AppHandle,
    db_path: &Path,
    vault_path: &Path,
    state: &mut SyncState,
) -> AppResult<SyncReport> {
    let start = std::time::Instant::now();
    let (obs_dir, sum_dir) = ensure_vault_dirs(vault_path)?;

    let conn = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)
        .map_err(|e| AppError::Sync(format!("open DB at {}: {}", db_path.display(), e)))?;

    let obs_written = observations::export(app, &conn, &obs_dir, state)?;
    let sum_written = summaries::export(app, &conn, &sum_dir, state)?;

    let duration_ms = start.elapsed().as_millis();
    let report = SyncReport {
        observations_written: obs_written,
        summaries_written: sum_written,
        duration_ms,
    };
    state.last_run_at = Some(Utc::now());
    state.last_run_report = Some(report.clone());
    Ok(report)
}

pub fn probe(db_path: &Path, state: &SyncState) -> AppResult<SyncPreview> {
    let conn = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    let new_observations: i64 = conn.query_row(
        "SELECT COUNT(*) FROM observations WHERE id > ?1",
        [state.last_observation_id],
        |row| row.get(0),
    )?;
    let new_summaries: i64 = conn.query_row(
        "SELECT COUNT(*) FROM session_summaries WHERE id > ?1",
        [state.last_summary_id],
        |row| row.get(0),
    )?;
    Ok(SyncPreview {
        new_observations,
        new_summaries,
    })
}

pub(crate) fn emit_progress(app: &AppHandle, kind: &'static str, current: u32, total: u32) {
    let _ = app.emit("sync:progress", SyncProgress { kind, current, total });
}
