use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use tauri::AppHandle;
use tauri_plugin_store::StoreExt;

use crate::error::{AppError, AppResult};

const STORE_PATH: &str = "settings.json";
const CONFIG_KEY: &str = "config";

#[derive(Serialize, Deserialize, Clone, Copy, Debug, Default)]
#[serde(rename_all = "lowercase")]
pub enum Theme {
    #[default]
    Auto,
    Light,
    Dark,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
#[serde(rename_all = "camelCase")]
pub struct Config {
    pub db_path: Option<PathBuf>,
    pub vault_path: Option<PathBuf>,
    pub interval_minutes: u32,
    pub theme: Theme,
    pub autostart: bool,
    pub schedule_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            db_path: None,
            vault_path: None,
            interval_minutes: 15,
            theme: Theme::default(),
            autostart: false,
            schedule_enabled: false,
        }
    }
}

pub fn load(app: &AppHandle) -> AppResult<Config> {
    let store = app
        .store(STORE_PATH)
        .map_err(|e| AppError::Config(format!("open store: {e}")))?;
    match store.get(CONFIG_KEY) {
        Some(value) => Ok(serde_json::from_value(value)?),
        None => Ok(Config::default()),
    }
}

pub fn save(app: &AppHandle, config: &Config) -> AppResult<()> {
    let store = app
        .store(STORE_PATH)
        .map_err(|e| AppError::Config(format!("open store: {e}")))?;
    store.set(CONFIG_KEY, serde_json::to_value(config)?);
    store
        .save()
        .map_err(|e| AppError::Config(format!("save store: {e}")))?;
    Ok(())
}
