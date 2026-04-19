use std::path::Path;

use rusqlite::Connection;
use tauri::AppHandle;

use super::{emit_progress, sanitize_filename, SyncState};
use crate::error::AppResult;

pub fn export(
    app: &AppHandle,
    conn: &Connection,
    sum_dir: &Path,
    state: &mut SyncState,
) -> AppResult<u32> {
    let total: i64 = conn.query_row(
        "SELECT COUNT(*) FROM session_summaries WHERE id > ?1",
        [state.last_summary_id],
        |row| row.get(0),
    )?;
    let total = total as u32;

    let mut stmt = conn.prepare(
        "SELECT id, project, created_at, request, investigated, learned,
                completed, next_steps, notes
         FROM session_summaries WHERE id > ?1 ORDER BY id ASC",
    )?;

    let mut rows = stmt.query([state.last_summary_id])?;
    let mut written: u32 = 0;

    while let Some(row) = rows.next()? {
        let id: i64 = row.get("id")?;
        let project: Option<String> = row.get("project")?;
        let created_at: Option<String> = row.get("created_at")?;
        let request: Option<String> = row.get("request")?;
        let investigated: Option<String> = row.get("investigated")?;
        let learned: Option<String> = row.get("learned")?;
        let completed: Option<String> = row.get("completed")?;
        let next_steps: Option<String> = row.get("next_steps")?;
        let notes: Option<String> = row.get("notes")?;

        let project = project.unwrap_or_else(|| "Global".to_string());
        let created_at = created_at.unwrap_or_default();
        let project_tag = project.to_lowercase().replace(' ', "-");

        let filename = sanitize_filename(&format!("{project}_Summary_{id}.md"));
        let filepath = sum_dir.join(filename);

        let content = format!(
            "---\n\
             id: {id}\n\
             project: {project}\n\
             created_at: {created_at}\n\
             tags:\n  - claude-memory\n  - summary\n  - {project_tag}\n\
             ---\n\
             # Session Summary: {project} ({id})\n\
             \n\
             ### Request\n\
             {request}\n\
             \n\
             ### Investigated\n\
             {investigated}\n\
             \n\
             ### Learned\n\
             {learned}\n\
             \n\
             ### Completed\n\
             {completed}\n\
             \n\
             ### Next Steps\n\
             {next_steps}\n\
             \n\
             ### Notes\n\
             {notes}\n",
            request = request.unwrap_or_default(),
            investigated = investigated.unwrap_or_default(),
            learned = learned.unwrap_or_default(),
            completed = completed.unwrap_or_default(),
            next_steps = next_steps.unwrap_or_default(),
            notes = notes.unwrap_or_default(),
        );

        std::fs::write(&filepath, content)?;
        state.last_summary_id = id;
        written += 1;
        emit_progress(app, "summary", written, total);
    }

    Ok(written)
}
