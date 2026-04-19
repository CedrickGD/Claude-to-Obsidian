import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import subprocess
import ctypes
from sync import SyncEngine

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Claude to Obsidian Sync")
        self.root.geometry("700x620")
        self.root.resizable(False, False)
        
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()
        
        # Windows 11 Fluent-ish Colors
        self.dark_bg = "#1c1c1c"
        self.dark_card = "#2d2d2d"
        self.dark_fg = "#ffffff"
        self.dark_accent = "#0078d4"
        
        self.light_bg = "#f3f3f3"
        self.light_card = "#ffffff"
        self.light_fg = "#000000"
        self.light_accent = "#005a9e"
        
        self.create_widgets()
        self.apply_theme()

    def set_title_bar_color(self, is_dark):
        """Toggle Windows Title Bar Dark/Light mode using DWM API."""
        try:
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            value = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
            # Refresh title bar
            self.root.withdraw()
            self.root.deiconify()
        except:
            pass

    def create_widgets(self):
        # Background Canvas
        self.bg_frame = tk.Frame(self.root)
        self.bg_frame.pack(fill=tk.BOTH, expand=True)

        # Main Content Container
        self.content = tk.Frame(self.bg_frame, padx=40, pady=30)
        self.content.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(self.content)
        header.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header, text="Claude ➜ Obsidian", font=("Segoe UI Variable Display", 22, "bold")).pack(side=tk.LEFT)
        self.theme_btn = tk.Button(header, text="🌙", command=self.toggle_theme, font=("Segoe UI", 14), 
                                   bd=0, relief="flat", cursor="hand2")
        self.theme_btn.pack(side=tk.RIGHT)

        # --- PATH SECTION ---
        self.db_card = self.create_card("Claude Memory Database", "db_path", self.browse_db)
        self.vault_card = self.create_card("Obsidian Vault", "vault_path", self.browse_vault)

        # --- SETTINGS SECTION ---
        self.settings_frame = tk.Frame(self.content)
        self.settings_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(self.settings_frame, text="Sync Settings", font=("Segoe UI Variable Small", 11, "bold")).pack(anchor="w")
        
        interval_row = tk.Frame(self.settings_frame)
        interval_row.pack(fill=tk.X, pady=5)
        
        tk.Label(interval_row, text="Update Interval:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.interval_entry = tk.Entry(interval_row, width=8, font=("Segoe UI", 10), relief="flat", highlightthickness=1)
        self.interval_entry.insert(0, str(self.config.get('interval', 10)))
        self.interval_entry.pack(side=tk.LEFT, padx=10)
        tk.Label(interval_row, text="minutes", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        # --- ACTION BUTTONS ---
        btn_frame = tk.Frame(self.content)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        self.btn_auto = self.create_action_button(btn_frame, "Auto-Detect Environments", self.auto_detect)
        self.btn_save = self.create_action_button(btn_frame, "Apply & Automate", self.setup_task, primary=True)
        self.btn_sync = self.create_action_button(btn_frame, "Manual Sync Now", self.run_sync)

        # Footer Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w", font=("Segoe UI", 9), padx=10, pady=8)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_card(self, title, config_key, cmd):
        card = tk.Frame(self.content, pady=10)
        card.pack(fill=tk.X, pady=5)
        
        tk.Label(card, text=title, font=("Segoe UI Variable Small", 10)).pack(anchor="w", padx=2)
        
        entry_row = tk.Frame(card)
        entry_row.pack(fill=tk.X, pady=2)
        
        entry = tk.Entry(entry_row, font=("Segoe UI", 10), relief="flat", highlightthickness=1)
        entry.insert(0, self.config.get(config_key, ''))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=4)
        
        btn = tk.Button(entry_row, text="Browse", command=cmd, font=("Segoe UI", 9), 
                        relief="flat", bd=0, padx=15, cursor="hand2")
        btn.pack(side=tk.RIGHT)
        
        setattr(self, f"{config_key}_entry", entry)
        return card

    def create_action_button(self, parent, text, cmd, primary=False):
        btn = tk.Button(parent, text=text, command=cmd, font=("Segoe UI", 10, "bold" if primary else "normal"),
                        relief="flat", bd=0, pady=10, cursor="hand2")
        btn.pack(fill=tk.X, pady=4)
        return btn

    def apply_theme(self):
        is_dark = self.config.get('theme') == "dark"
        bg = self.dark_bg if is_dark else self.light_bg
        card_bg = self.dark_card if is_dark else self.light_card
        fg = self.dark_fg if is_dark else self.light_fg
        accent = self.dark_accent if is_dark else self.light_accent
        
        self.set_title_bar_color(is_dark)
        
        self.bg_frame.configure(bg=bg)
        self.content.configure(bg=bg)
        self.status_bar.configure(bg=card_bg, fg=fg)
        self.theme_btn.configure(text="☀️" if is_dark else "🌙", bg=bg, fg=fg, activebackground=bg, activeforeground=fg)
        
        self.style_recursive(self.content, bg, card_bg, fg, accent)

    def style_recursive(self, parent, bg, card_bg, fg, accent):
        for widget in parent.winfo_children():
            w_class = widget.winfo_class()
            
            if w_class == "Frame":
                widget.configure(bg=bg)
                self.style_recursive(widget, bg, card_bg, fg, accent)
            elif w_class == "Label":
                widget.configure(bg=bg, fg=fg)
            elif w_class == "Entry":
                widget.configure(bg=card_bg, fg=fg, insertbackground=fg, 
                                 highlightbackground=accent if bg == self.dark_bg else "#cccccc", 
                                 highlightcolor=accent, bd=0)
            elif w_class == "Button":
                if widget == self.btn_save:
                    widget.configure(bg=accent, fg="white", activebackground=accent)
                else:
                    widget.configure(bg=card_bg, fg=fg, activebackground=bg, activeforeground=fg)
            
            # Special case for card rows (they should have bg)
            if parent in [self.db_card, self.vault_card, self.settings_frame]:
                parent.configure(bg=bg)

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
        self.config['theme'] = self.config.get('theme', 'dark')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def toggle_theme(self):
        self.config['theme'] = "light" if self.config.get('theme') == "dark" else "dark"
        self.apply_theme()
        self.save_config()

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
    # Fix High DPI scaling
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root = tk.Tk()
    app = App(root)
    root.mainloop()
