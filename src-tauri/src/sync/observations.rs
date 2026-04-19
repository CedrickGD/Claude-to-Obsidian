use std::path::Path;

use rusqlite::Connection;
use tauri::AppHandle;

use super::{emit_progress, sanitize_filename, SyncState};
use crate::error::AppResult;

pub fn export(
    app: &AppHandle,
    conn: &Connection,
    obs_dir: &Path,
    state: &mut SyncState,
) -> AppResult<u32> {
    let total: i64 = conn.query_row(
        "SELECT COUNT(*) FROM observations WHERE id > ?1",
        [state.last_observation_id],
        |row| row.get(0),
    )?;
    let total = total as u32;

    let mut stmt = conn.prepare(
        "SELECT id, project, title, subtitle, type, created_at, narrative,
                facts, concepts, files_read, files_modified
         FROM observations WHERE id > ?1 ORDER BY id ASC",
    )?;

    let mut rows = stmt.query([state.last_observation_id])?;
    let mut written: u32 = 0;

    while let Some(row) = rows.next()? {
        let id: i64 = row.get("id")?;
        let project: Option<String> = row.get("project")?;
        let title: Option<String> = row.get("title")?;
        let subtitle: Option<String> = row.get("subtitle")?;
        let obs_type: Option<String> = row.get("type")?;
        let created_at: Option<String> = row.get("created_at")?;
        let narrative: Option<String> = row.get("narrative")?;
        let facts_raw: Option<String> = row.get("facts")?;
        let concepts_raw: Option<String> = row.get("concepts")?;
        let files_read: Option<String> = row.get("files_read")?;
        let files_modified: Option<String> = row.get("files_modified")?;

        let project = project.unwrap_or_else(|| "Global".to_string());
        let title = title.unwrap_or_else(|| format!("Observation {id}"));
        let subtitle = subtitle.unwrap_or_default();
        let obs_type = obs_type.unwrap_or_default();
        let created_at = created_at.unwrap_or_default();
        let narrative = narrative.unwrap_or_else(|| "No narrative provided.".to_string());

        let facts: Vec<String> = facts_raw
            .as_deref()
            .filter(|s| !s.is_empty())
            .and_then(|s| serde_json::from_str(s).ok())
            .unwrap_or_default();
        let concepts: Vec<String> = concepts_raw
            .as_deref()
            .filter(|s| !s.is_empty())
            .and_then(|s| serde_json::from_str(s).ok())
            .unwrap_or_default();

        let title_safe: String = title.chars().take(50).collect();
        let filename = sanitize_filename(&format!("{project}_{id}_{title_safe}.md"));
        let filepath = obs_dir.join(filename);

        let facts_md = if facts.is_empty() {
            String::new()
        } else {
            facts
                .iter()
                .map(|f| format!("- {f}"))
                .collect::<Vec<_>>()
                .join("\n")
        };
        let concepts_md = concepts.join(", ");
        let project_tag = project.to_lowercase().replace(' ', "-");

        let content = format!(
            "---\n\
             id: {id}\n\
             project: {project}\n\
             type: {obs_type}\n\
             created_at: {created_at}\n\
             tags:\n  - claude-memory\n  - observation\n  - {project_tag}\n\
             ---\n\
             # {title}\n\
             ## {subtitle}\n\
             \n\
             ### Narrative\n\
             {narrative}\n\
             \n\
             ### Facts\n\
             {facts_md}\n\
             \n\
             ### Concepts\n\
             {concepts_md}\n\
             \n\
             ---\n\
             **Metadata:**\n\
             - **Files Read:** {files_read}\n\
             - **Files Modified:** {files_modified}\n",
            files_read = files_read.unwrap_or_default(),
            files_modified = files_modified.unwrap_or_default(),
        );

        std::fs::write(&filepath, content)?;
        state.last_observation_id = id;
        written += 1;
        emit_progress(app, "observation", written, total);
    }

    Ok(written)
}
