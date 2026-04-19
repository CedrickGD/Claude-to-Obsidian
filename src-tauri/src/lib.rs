mod autodetect;
mod config;
mod error;
mod scheduler;
mod sync;
mod vault;

use std::path::{Path, PathBuf};

use tauri::{AppHandle, Manager};

use crate::autodetect::AutoDetectResult;
use crate::config::Config;
use crate::error::{AppError, AppResult};
use crate::sync::{SyncPreview, SyncReport, SyncState};

fn state_file_path(app: &AppHandle) -> AppResult<PathBuf> {
    Ok(app.path().app_config_dir()?.join("sync_state.json"))
}

#[tauri::command]
async fn load_config(app: AppHandle) -> AppResult<Config> {
    config::load(&app)
}

#[tauri::command]
async fn save_config(app: AppHandle, config: Config) -> AppResult<()> {
    config::save(&app, &config)
}

#[tauri::command]
async fn auto_detect() -> AppResult<AutoDetectResult> {
    tauri::async_runtime::spawn_blocking(|| Ok(autodetect::detect()))
        .await
        .map_err(|e| AppError::Sync(format!("task join: {e}")))?
}

#[tauri::command]
async fn create_vault(parent_dir: String, vault_name: String) -> AppResult<PathBuf> {
    tauri::async_runtime::spawn_blocking(move || {
        vault::create(Path::new(&parent_dir), &vault_name)
    })
    .await
    .map_err(|e| AppError::Sync(format!("task join: {e}")))?
}

#[tauri::command]
async fn run_sync(
    app: AppHandle,
    db_path: String,
    vault_path: String,
) -> AppResult<SyncReport> {
    let state_path = state_file_path(&app)?;
    let app_handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || -> AppResult<SyncReport> {
        let mut state = SyncState::load(&state_path)?;
        let report = sync::run_once(
            &app_handle,
            Path::new(&db_path),
            Path::new(&vault_path),
            &mut state,
        )?;
        state.save(&state_path)?;
        Ok(report)
    })
    .await
    .map_err(|e| AppError::Sync(format!("task join: {e}")))?
}

#[tauri::command]
async fn probe_sync(app: AppHandle, db_path: String) -> AppResult<SyncPreview> {
    let state_path = state_file_path(&app)?;
    tauri::async_runtime::spawn_blocking(move || -> AppResult<SyncPreview> {
        let state = SyncState::load(&state_path)?;
        sync::probe(Path::new(&db_path), &state)
    })
    .await
    .map_err(|e| AppError::Sync(format!("task join: {e}")))?
}

#[tauri::command]
async fn last_sync_state(app: AppHandle) -> AppResult<SyncState> {
    let state_path = state_file_path(&app)?;
    tauri::async_runtime::spawn_blocking(move || SyncState::load(&state_path))
        .await
        .map_err(|e| AppError::Sync(format!("task join: {e}")))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri_subscriber_init();

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--minimized"]),
        ))
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                scheduler::run_loop(handle).await;
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            load_config,
            save_config,
            auto_detect,
            create_vault,
            run_sync,
            probe_sync,
            last_sync_state,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn tauri_subscriber_init() {
    let _ = tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .with_target(false)
        .try_init();
}
