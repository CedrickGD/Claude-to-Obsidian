use std::path::PathBuf;
use std::time::Duration;

use tauri::{AppHandle, Manager};

use crate::sync::{self, SyncState};

fn state_path_for(app: &AppHandle) -> Option<PathBuf> {
    app.path()
        .app_config_dir()
        .ok()
        .map(|d| d.join("sync_state.json"))
}

pub async fn run_loop(app: AppHandle) {
    // Poll config every 30s while disabled. When enabled, sleep the configured interval, then sync.
    let poll = Duration::from_secs(30);

    loop {
        let cfg = crate::config::load(&app).unwrap_or_default();

        if !cfg.schedule_enabled {
            tokio::time::sleep(poll).await;
            continue;
        }

        let (db_path, vault_path) = match (cfg.db_path.clone(), cfg.vault_path.clone()) {
            (Some(d), Some(v)) if d.exists() && v.exists() => (d, v),
            _ => {
                tokio::time::sleep(poll).await;
                continue;
            }
        };

        let interval = Duration::from_secs((cfg.interval_minutes as u64).max(1) * 60);
        tokio::time::sleep(interval).await;

        let state_path = match state_path_for(&app) {
            Some(p) => p,
            None => continue,
        };

        let app_clone = app.clone();
        let _ = tauri::async_runtime::spawn_blocking(move || {
            let mut state = SyncState::load(&state_path).unwrap_or_default();
            match sync::run_once(&app_clone, &db_path, &vault_path, &mut state) {
                Ok(report) => {
                    tracing::info!(
                        obs = report.observations_written,
                        sum = report.summaries_written,
                        "scheduled sync complete"
                    );
                    if let Err(e) = state.save(&state_path) {
                        tracing::warn!("scheduled sync: save state failed: {e}");
                    }
                }
                Err(e) => tracing::warn!("scheduled sync failed: {e}"),
            }
        })
        .await;
    }
}
