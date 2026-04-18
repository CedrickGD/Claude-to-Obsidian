import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
from sync import SyncEngine

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude to Obsidian Sync")
        self.root.geometry("600x400")
        
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()

        # UI Elements
        tk.Label(root, text="Claude Memory Database Path:").pack(pady=5)
        self.db_entry = tk.Entry(root, width=70)
        self.db_entry.insert(0, self.config.get('db_path', ''))
        self.db_entry.pack()
        tk.Button(root, text="Browse", command=self.browse_db).pack()

        tk.Label(root, text="Obsidian Vault Path:").pack(pady=5)
        self.vault_entry = tk.Entry(root, width=70)
        self.vault_entry.insert(0, self.config.get('vault_path', ''))
        self.vault_entry.pack()
        tk.Button(root, text="Browse", command=self.browse_vault).pack()

        tk.Button(root, text="Auto-Detect Obsidian", command=self.auto_detect).pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Run Sync Now", command=self.run_sync, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Setup Scheduled Task (10m)", command=self.setup_task, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        self.config['db_path'] = self.db_entry.get()
        self.config['vault_path'] = self.vault_entry.get()
        self.config['state_path'] = os.path.join(os.path.dirname(__file__), 'sync_state.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo("Success", "Configuration saved!")

    def browse_db(self):
        path = filedialog.askopenfilename(title="Select claude-mem.db", filetypes=[("SQLite DB", "*.db")])
        if path:
            self.db_entry.delete(0, tk.END)
            self.db_entry.insert(0, path)

    def browse_vault(self):
        path = filedialog.askdirectory(title="Select Obsidian Vault Folder")
        if path:
            self.vault_entry.delete(0, tk.END)
            self.vault_entry.insert(0, path)

    def auto_detect(self):
        # Check standard Claude path
        user_home = os.path.expanduser("~")
        claude_db = os.path.join(user_home, ".claude-mem", "claude-mem.db")
        if os.path.exists(claude_db):
            self.db_entry.delete(0, tk.END)
            self.db_entry.insert(0, claude_db)
            
        # Check Obsidian config
        obs_json = os.path.join(os.getenv('APPDATA'), "obsidian", "obsidian.json")
        if os.path.exists(obs_json):
            try:
                with open(obs_json, 'r') as f:
                    data = json.load(f)
                    vaults = data.get('vaults', {})
                    if vaults:
                        # Grab first vault found
                        v_path = list(vaults.values())[0]['path']
                        self.vault_entry.delete(0, tk.END)
                        self.vault_entry.insert(0, v_path)
                        messagebox.showinfo("Detected", "Paths detected automatically!")
            except:
                pass

    def run_sync(self):
        self.save_config()
        try:
            engine = SyncEngine(self.config_path)
            result = engine.run()
            messagebox.showinfo("Sync Result", result)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_task(self):
        self.save_config()
        script_path = os.path.abspath(__file__.replace('main.py', 'sync.py'))
        python_exe = "python.exe"
        task_name = "ClaudeMemoriesToObsidian"
        
        cmd = f'powershell.exe -Command "$Action = New-ScheduledTaskAction -Execute \'{python_exe}\' -Argument \'{script_path}\'; $Trigger = New-ScheduledTaskTrigger -At (Get-Date) -Once -RepetitionInterval (New-TimeSpan -Minutes 10); Register-ScheduledTask -TaskName \'{task_name}\' -Action $Action -Trigger $Trigger -Force"'
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            messagebox.showinfo("Success", "Scheduled task created/updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create task: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
