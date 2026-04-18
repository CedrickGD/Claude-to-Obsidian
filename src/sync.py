import sqlite3
import os
import json
import re
from datetime import datetime

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

class SyncEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config()
        self.ensure_dirs()

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
        self.db_path = self.config['db_path']
        self.vault_path = self.config['vault_path']
        self.memories_dir = os.path.join(self.vault_path, 'Claude Memories')
        self.state_path = self.config.get('state_path', 'sync_state.json')

    def load_state(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                return json.load(f)
        return {"last_observation_id": 0, "last_summary_id": 0}

    def save_state(self, state):
        with open(self.state_path, 'w') as f:
            json.dump(state, f)

    def ensure_dirs(self):
        os.makedirs(os.path.join(self.memories_dir, 'Observations'), exist_ok=True)
        os.makedirs(os.path.join(self.memories_dir, 'Summaries'), exist_ok=True)

    def export_observations(self, cursor, state):
        cursor.execute("SELECT * FROM observations WHERE id > ? ORDER BY id ASC", (state["last_observation_id"],))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            data = dict(zip(columns, row))
            obs_id = data['id']
            project = data['project'] or "Global"
            title = data['title'] or f"Observation {obs_id}"
            
            filename = sanitize_filename(f"{project}_{obs_id}_{title[:50]}.md")
            filepath = os.path.join(self.memories_dir, 'Observations', filename)
            
            facts = json.loads(data['facts']) if data['facts'] else []
            concepts = json.loads(data['concepts']) if data['concepts'] else []
            
            content = f"""---
id: {obs_id}
project: {project}
type: {data['type']}
created_at: {data['created_at']}
tags:
  - claude-memory
  - observation
  - {project.lower()}
---
# {title}
## {data['subtitle']}

### Narrative
{data['narrative'] or "No narrative provided."}

### Facts
{chr(10).join([f"- {f}" for f in facts])}

### Concepts
{", ".join(concepts)}

---
**Metadata:**
- **Files Read:** {data['files_read']}
- **Files Modified:** {data['files_modified']}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            state["last_observation_id"] = obs_id

    def export_summaries(self, cursor, state):
        cursor.execute("SELECT * FROM session_summaries WHERE id > ? ORDER BY id ASC", (state["last_summary_id"],))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            data = dict(zip(columns, row))
            sum_id = data['id']
            project = data['project'] or "Global"
            
            filename = sanitize_filename(f"{project}_Summary_{sum_id}.md")
            filepath = os.path.join(self.memories_dir, 'Summaries', filename)
            
            content = f"""---
id: {sum_id}
project: {project}
created_at: {data['created_at']}
tags:
  - claude-memory
  - summary
  - {project.lower()}
---
# Session Summary: {project} ({sum_id})

### Request
{data['request']}

### Investigated
{data['investigated']}

### Learned
{data['learned']}

### Completed
{data['completed']}

### Next Steps
{data['next_steps']}

### Notes
{data['notes']}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            state["last_summary_id"] = sum_id

    def run(self):
        state = self.load_state()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            self.export_observations(cursor, state)
            self.export_summaries(cursor, state)
            self.save_state(state)
            return f"Sync complete. Observations: {state['last_observation_id']}, Summaries: {state['last_summary_id']}"
        finally:
            conn.close()

if __name__ == "__main__":
    # For CLI usage
    script_dir = os.path.dirname(os.path.abspath(__file__))
    engine = SyncEngine(os.path.join(script_dir, 'config.json'))
    print(engine.run())
