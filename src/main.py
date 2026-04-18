import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import subprocess
from sync import SyncEngine

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude to Obsidian Sync")
        self.root.geometry("700x550")
        
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()
        
        # Theme Colors
        self.dark_bg = "#1e1e1e"
        self.dark_fg = "#ffffff"
        self.dark_btn = "#333333"
        self.light_bg = "#f3f3f3"
        self.light_fg = "#000000"
        self.light_btn = "#e1e1e1"
        
        self.setup_styles()
        self.create_widgets()
        self.apply_theme()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
    def create_widgets(self):
        # Container
        self.main_frame = tk.Frame(self.root, padx=30, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.main_frame.cget("bg"))
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="Claude ➜ Obsidian", font=("Segoe UI Semibold", 18)).pack(side=tk.LEFT)
        self.theme_btn = tk.Button(header_frame, text="🌙", command=self.toggle_theme, font=("Segoe UI", 12), bd=0, cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT)

        # Paths Section
        self.create_path_row("Claude Memory DB:", 'db_path', self.browse_db)
        self.create_path_row("Obsidian Vault:", 'vault_path', self.browse_vault)

        # Settings Section
        settings_label = tk.Label(self.main_frame, text="Automation Settings", font=("Segoe UI Semibold", 12))
        settings_label.pack(anchor="w", pady=(20, 10))
        
        sync_frame = tk.Frame(self.main_frame)
        sync_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(sync_frame, text="Sync Interval (minutes):", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.interval_entry = tk.Entry(sync_frame, width=10, font=("Segoe UI", 10))
        self.interval_entry.insert(0, str(self.config.get('interval', 10)))
        self.interval_entry.pack(side=tk.LEFT, padx=10)

        # Actions
        btn_container = tk.Frame(self.main_frame)
        btn_container.pack(fill=tk.X, pady=30)

        self.btn_auto = tk.Button(btn_container, text="Auto-Detect Paths", command=self.auto_detect, font=("Segoe UI", 10), height=2)
        self.btn_auto.pack(fill=tk.X, pady=5)

        self.btn_save = tk.Button(btn_container, text="Save & Update Automation", command=self.setup_task, bg="#0078d4", fg="white", font=("Segoe UI", 10, "bold"), height=2)
        self.btn_save.pack(fill=tk.X, pady=5)
        
        self.btn_sync = tk.Button(btn_container, text="Sync Now", command=self.run_sync, font=("Segoe UI", 10), height=2)
        self.btn_sync.pack(fill=tk.X, pady=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Segoe UI", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_path_row(self, label_text, config_key, browse_cmd):
        frame = tk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=10)
        
        tk.Label(frame, text=label_text, font=("Segoe UI", 10)).pack(anchor="w")
        
        entry_frame = tk.Frame(frame)
        entry_frame.pack(fill=tk.X, pady=2)
        
        entry = tk.Entry(entry_frame, font=("Segoe UI", 10))
        entry.insert(0, self.config.get(config_key, ''))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn = tk.Button(entry_frame, text="Browse", command=browse_cmd, font=("Segoe UI", 9))
        btn.pack(side=tk.RIGHT)
        
        setattr(self, f"{config_key}_entry", entry)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"theme": "dark", "interval": 10}

    def save_config(self):
        self.config['db_path'] = self.db_path_entry.get()
        self.config['vault_path'] = self.vault_path_entry.get()
        self.config['interval'] = int(self.interval_entry.get() if self.interval_entry.get() else 10)
        self.config['state_path'] = os.path.join(os.path.dirname(__file__), 'sync_state.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def toggle_theme(self):
        self.config['theme'] = "light" if self.config.get('theme') == "dark" else "dark"
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        is_dark = self.config.get('theme') == "dark"
        bg = self.dark_bg if is_dark else self.light_bg
        fg = self.dark_fg if is_dark else self.light_fg
        btn_bg = self.dark_btn if is_dark else self.light_btn
        
        self.root.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        self.theme_btn.configure(text="☀️" if is_dark else "🌙", bg=bg, fg=fg)
        
        self.color_widget(self.main_frame, bg, fg, btn_bg)
        self.status_bar.configure(bg=btn_bg, fg=fg)

    def color_widget(self, widget, bg, fg, btn_bg):
        w_type = widget.winfo_class()
        
        try:
            # All widgets get a background
            widget.configure(bg=bg)
            
            # Only certain widgets get a foreground
            if w_type in ("Label", "Button", "Entry"):
                widget.configure(fg=fg)
                
            if w_type == "Button" and widget != self.btn_save:
                widget.configure(bg=btn_bg, activebackground=bg, activeforeground=fg)
            elif w_type == "Entry":
                widget.configure(bg=btn_bg, insertbackground=fg)
        except:
            pass # Ignore options not supported by specific widget types
            
        for child in widget.winfo_children():
            self.color_widget(child, bg, fg, btn_bg)

    def browse_db(self):
        path = filedialog.askopenfilename(title="Select claude-mem.db", filetypes=[("SQLite DB", "*.db")])
        if path:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, path)

    def browse_vault(self):
        path = filedialog.askdirectory(title="Select Obsidian Vault Folder")
        if path:
            self.vault_path_entry.delete(0, tk.END)
            self.vault_path_entry.insert(0, path)

    def auto_detect(self):
        user_home = os.path.expanduser("~")
        claude_db = os.path.join(user_home, ".claude-mem", "claude-mem.db")
        if os.path.exists(claude_db):
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, claude_db)
            
        obs_json = os.path.join(os.getenv('APPDATA'), "obsidian", "obsidian.json")
        if os.path.exists(obs_json):
            try:
                with open(obs_json, 'r') as f:
                    data = json.load(f)
                    vaults = data.get('vaults', {})
                    if vaults:
                        v_path = list(vaults.values())[0]['path']
                        self.vault_path_entry.delete(0, tk.END)
                        self.vault_path_entry.insert(0, v_path)
                        self.status_var.set("Paths detected!")
            except: pass

    def run_sync(self):
        self.save_config()
        try:
            engine = SyncEngine(self.config_path)
            result = engine.run()
            self.status_var.set(result)
            messagebox.showinfo("Sync Result", result)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_task(self):
        try:
            self.save_config()
            interval = int(self.interval_entry.get())
            script_path = os.path.abspath(__file__.replace('main.py', 'sync.py'))
            python_exe = "pythonw.exe"
            task_name = "ClaudeMemoriesToObsidian"
            
            subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, capture_output=True)
            
            cmd = f'powershell.exe -Command "$Action = New-ScheduledTaskAction -Execute \'{python_exe}\' -Argument \'{script_path}\'; $Trigger = New-ScheduledTaskTrigger -At (Get-Date) -Once -RepetitionInterval (New-TimeSpan -Minutes {interval}); Register-ScheduledTask -TaskName \'{task_name}\' -Action $Action -Trigger $Trigger -Force"'
            
            subprocess.run(cmd, shell=True, check=True)
            self.status_var.set(f"Automation set to {interval}m")
            messagebox.showinfo("Success", f"Task scheduled every {interval} minutes using pythonw (silent).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create task: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
