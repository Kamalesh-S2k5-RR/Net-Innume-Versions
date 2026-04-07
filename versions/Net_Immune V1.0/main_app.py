import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
import os
import sys
import subprocess
import pyperclip
import psutil
import ctypes
import json
import webbrowser
import urllib.parse
import tkinter.messagebox
from groq import Groq
from plyer import notification

# --- FILE PATHS & CONFIGURATION ---
WATCH_FOLDER = "Threat_Dropzone"
LOGS_FOLDER = "Logs"
CONFIG_FILE = "config.json"
STATS_FILE = "stats.json"

for folder in [WATCH_FOLDER, LOGS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- DATA MANAGEMENT ---
def load_data(filepath, default_data):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f: return json.load(f)
        except: return default_data
    return default_data

def save_data(filepath, data):
    with open(filepath, "w") as f: json.dump(data, f, indent=4)

# --- SYSTEM REBOOT LOGIC ---
mutex_handle = None

def reboot_app():
    global mutex_handle
    if mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
        ctypes.windll.kernel32.CloseHandle(mutex_handle)
        
    try:
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + sys.argv[1:]) 
        else:
            subprocess.Popen([sys.executable] + sys.argv)     
    except Exception: pass
    os._exit(0) 

# --- ADVANCED STATS ENGINE ---
def update_stats(is_threat):
    stats = load_data(STATS_FILE, {"all_time": {"safe": 0, "threats": 0}, "history": {}})
    
    if "safe" in stats and isinstance(stats["safe"], int):
        stats = {"all_time": {"safe": stats.get("safe", 0), "threats": stats.get("threats", 0)}, "history": {}}

    today = time.strftime("%Y-%m-%d")
    if today not in stats["history"]:
        stats["history"][today] = {"safe": 0, "threats": 0}

    if is_threat:
        stats["all_time"]["threats"] += 1
        stats["history"][today]["threats"] += 1
    else:
        stats["all_time"]["safe"] += 1
        stats["history"][today]["safe"] += 1

    save_data(STATS_FILE, stats)

# --- BULLETPROOF NOTIFICATIONS ---
def send_alert(title, message):
    safe_message = message[:250] + "..." if len(message) > 250 else message
    try:
        icon_path = os.path.abspath(resource_path("mascot.ico"))
        if not os.path.exists(icon_path): icon_path = None
        notification.notify(title=title, message=safe_message, app_name='Net Immune', app_icon=icon_path, timeout=5)
    except Exception:
        try:
            notification.notify(title=title, message=safe_message, app_name='Net Immune', timeout=5)
        except Exception: pass

# --- SANITIZED LOGS ---
def write_to_log(agent_name, entry):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    filepath = os.path.join(LOGS_FOLDER, f"{agent_name}_log.txt")
    safe_entry = entry.replace('\n', ' ').replace('\r', '') 
    with open(filepath, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {safe_entry}\n")

# --- ORIGINAL, UNINTERRUPTED AI LOGIC ---
def analyze_threat(prompt_type, text_to_analyze):
    config = load_data(CONFIG_FILE, {"api_key": "", "theme": "dark"})
    api_key = config.get("api_key", "")
    
    if not api_key: return "[ERROR] Missing API Key."
    client = Groq(api_key=api_key)
    
    if prompt_type == "clipboard": sys_prompt = "Categorize text into EXACTLY ONE tag: [SAFE], [SUSPICIOUS], [PHISHING], [SCAM], [EXTORTION], [MALICIOUS]. Format exactly: [TAG] Reason."
    elif prompt_type == "file": sys_prompt = "Categorize file content into EXACTLY ONE tag: [SAFE], [MALWARE], [HACK_ATTACK]. Format exactly: [TAG] Reason."
    elif prompt_type == "network": sys_prompt = "Categorize active network ports into EXACTLY ONE tag: [SAFE], [SUSPICIOUS], [MALICIOUS]. Format exactly: [TAG] Reason."
    elif prompt_type == "process": sys_prompt = "Analyze these high-CPU Windows processes. Categorize into EXACTLY ONE tag: [SAFE], [SUSPICIOUS], [MALICIOUS]. Format exactly: [TAG] Reason. Flag known crypto-miners or obvious malware names."
    else: sys_prompt = "Analyze the list of files found on this newly inserted USB drive. Look for dangerous executable extensions (.bat, .vbs, .exe, .sh) or auto-run scripts. If it just contains normal folders or documents, mark it SAFE. Categorize into EXACTLY ONE tag: [SAFE], [SUSPICIOUS]. Format exactly: [TAG] Reason."
        
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are 'Net Immune', a cybersecurity agent. " + sys_prompt}, 
                      {"role": "user", "content": text_to_analyze}],
            model="llama-3.3-70b-versatile",
        )
        result = response.choices[0].message.content.strip()
        if "[ERROR]" not in result.upper():
            update_stats("[SAFE]" not in result.upper())
        return result
    except Exception as e: 
        return f"[ERROR] API Connection Failed: {e}"

# --- FIRST TIME SETUP WIZARD ---
class SetupWizard:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Net Immune - Initial Setup")
        self.root.geometry("480x520") 
        self.root.resizable(False, False)
        self.root.configure(fg_color=("#F0F0F0", "#000000")) 
        
        try:
            icon_img = tk.PhotoImage(file=resource_path("mascot.png"))
            self.root.iconphoto(False, icon_img)
        except: pass

        ctk.CTkLabel(self.root, text="WELCOME TO NET IMMUNE", font=("Courier New", 20, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(20, 10))

        api_frame = ctk.CTkFrame(self.root, fg_color=("#E0E0E0", "#111111"))
        api_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(api_frame, text="🧠 AI Brain Setup", font=("Arial", 16, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(15, 5))
        
        instructions = (
            "Net Immune requires a free Llama-3 API Key to scan for threats.\n\n"
            "1. Click the button below to open the Groq Console.\n"
            "2. Create a free account and generate a new API key.\n"
            "3. ⚠️ IMPORTANT: Copy and save your key in a Notepad! "
            "The website will hide it forever once you close the window.\n"
            "4. Paste your key below and press Enter."
        )
        ctk.CTkLabel(api_frame, text=instructions, font=("Arial", 12), text_color=("#000000", "#FFFFFF"), justify="left", wraplength=400).pack(padx=20, pady=10)
        
        ctk.CTkButton(api_frame, text="🔗 Get My Free API Key", fg_color="#0055AA", text_color="#FFFFFF", hover_color="#0077CC", command=lambda: webbrowser.open("https://console.groq.com/keys")).pack(pady=10)
        
        self.api_entry = ctk.CTkEntry(api_frame, placeholder_text="Paste your API Key here (Right-Click to Paste)", width=380, show="*")
        self.api_entry.pack(pady=(5, 5))

        self.api_entry.bind("<Return>", self.save_and_start)

        self.right_click_menu = tk.Menu(self.root, tearoff=False, bg="#333333", fg="#FFFFFF", font=("Arial", 10), activebackground="#0055AA", activeforeground="#FFFFFF")
        self.right_click_menu.add_command(label="📋 Paste", command=self.paste_key)
        self.right_click_menu.add_command(label="❌ Clear", command=lambda: self.api_entry.delete(0, "end"))
        self.api_entry.bind("<Button-3>", self.show_context_menu)

        self.error_label = ctk.CTkLabel(api_frame, text="", text_color="#FF4444", font=("Arial", 12, "bold"))
        self.error_label.pack(pady=(0, 10))

        self.verify_btn = ctk.CTkButton(self.root, text="VERIFY & INITIATE SYSTEM", fg_color="#00AA55", text_color="#FFFFFF", hover_color="#00CC66", height=40, font=("Arial", 14, "bold"), command=self.save_and_start)
        self.verify_btn.pack(pady=20)

    def show_context_menu(self, event):
        try:
            self.right_click_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.right_click_menu.grab_release()

    def paste_key(self):
        try:
            text = pyperclip.paste()
            self.api_entry.delete(0, "end") 
            self.api_entry.insert("insert", text)
        except Exception: pass

    def save_and_start(self, event=None):
        key = self.api_entry.get().strip()
        self.verify_btn.configure(state="disabled") 
        
        if not key.startswith("gsk_"):
            self.error_label.configure(text="❌ Invalid Format! Groq keys must start with 'gsk_'")
            self.verify_btn.configure(state="normal")
            return

        self.error_label.configure(text="⏳ Verifying connection to AI Server...", text_color="#00FFCC")
        self.root.update()

        try:
            client = Groq(api_key=key)
            client.models.list() 
            
            config = load_data(CONFIG_FILE, {"theme": "dark"})
            config["api_key"] = key
            config["show_tutorial"] = True 
            save_data(CONFIG_FILE, config)
            
            self.error_label.configure(text="✅ Verification Successful!", text_color="#00AA55")
            self.root.update()
            time.sleep(0.5)
            
            reboot_app() 
        except Exception:
            self.error_label.configure(text="❌ API Key Rejected! Make sure you copied it correctly.", text_color="#FF4444")
            self.verify_btn.configure(state="normal")

# --- MAIN APPLICATION DASHBOARD ---
class DashboardWindow:
    def __init__(self, mascot):
        self.mascot = mascot
        self.window = ctk.CTkToplevel()
        self.window.title("Net Immune Core")
        self.window.geometry("350x640") 
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)
        self.window.configure(fg_color=("#F0F0F0", "#181818"))

        try:
            icon_img = tk.PhotoImage(file=resource_path("mascot.png"))
            self.window.iconphoto(False, icon_img)
        except Exception: pass

        x = mascot.root.winfo_x() - 125
        y = mascot.root.winfo_y() + 110
        self.window.geometry(f"+{x}+{y}")

        self.main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        self.settings_frame = ctk.CTkFrame(self.window, fg_color="transparent")

        self.build_main_frame()
        self.build_settings_frame()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        config = load_data(CONFIG_FILE, {})
        if config.get("show_tutorial", False):
            config["show_tutorial"] = False
            save_data(CONFIG_FILE, config)
            self.window.after(800, self.show_tutorial_popup)

    def show_tutorial_popup(self):
        self.tut_win = ctk.CTkToplevel(self.window)
        self.tut_win.title("Quick Start Guide")
        self.tut_win.geometry("380x420+-10000+-10000")
        self.tut_win.attributes("-alpha", 0.0) 
        
        self.tut_win.transient(self.window) 
        self.tut_win.grab_set()             
        self.tut_win.focus_force()          
        self.tut_win.attributes("-topmost", True)
        self.tut_win.resizable(False, False)
        self.tut_win.configure(fg_color=("#F5F5F5", "#1E1E1E"))

        ctk.CTkLabel(self.tut_win, text="Welcome to Net Immune!", font=("Courier New", 18, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(15, 2))
        ctk.CTkLabel(self.tut_win, text="Your AI-Powered Cybersecurity Shield", font=("Arial", 12, "italic"), text_color=("#555555", "#AAAAAA")).pack(pady=(0, 15))
        
        guide_frame = ctk.CTkFrame(self.tut_win, fg_color=("#E0E0E0", "#2A2A2A"), corner_radius=10)
        guide_frame.pack(padx=20, pady=5, fill="x")

        agents = [
            ("📋 Clipboard:", "Scans copied text/links for phishing."),
            ("📁 Dropzone:", "Drop files here to scan for malware."),
            ("🌐 Network:", "Monitors active ports for bad connections."),
            ("💾 USB Drive:", "Auto-scans external drives on insertion."),
            ("⚙️ Process:", "Watches memory for suspicious activity.")
        ]

        for icon_title, desc in agents:
            row_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=6)
            ctk.CTkLabel(row_frame, text=icon_title, font=("Arial", 13, "bold"), text_color=("#000000", "#FFFFFF"), width=110, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=desc, font=("Arial", 12), text_color=("#333333", "#CCCCCC"), anchor="w").pack(side="left", fill="x", expand=True)

        pro_tip = "🚨 Pro Tip: If the floating bot turns RED, a threat was blocked! You can safely review it in the Logs."
        ctk.CTkLabel(self.tut_win, text=pro_tip, font=("Arial", 12, "bold"), text_color=("#CC0000", "#FF6666"), wraplength=340, justify="center").pack(pady=(15, 10), padx=10)
        
        ctk.CTkButton(self.tut_win, text="Got it! Secure my system", font=("Arial", 14, "bold"), fg_color="#00AA55", text_color="#FFFFFF", hover_color="#00CC66", command=self.fade_out_tutorial).pack(pady=(10, 20))

        self.tut_win.update_idletasks()
        x = self.window.winfo_x() - 15
        y = self.window.winfo_y() + 50
        self.tut_win.geometry(f"+{x}+{y}")

        self.tut_alpha = 0.0
        self.fade_in_tutorial()

    def fade_in_tutorial(self):
        if not self.tut_win.winfo_exists(): return
        self.tut_alpha += 0.1
        if self.tut_alpha < 1.0:
            self.tut_win.attributes("-alpha", self.tut_alpha)
            self.tut_win.after(20, self.fade_in_tutorial)
        else:
            self.tut_win.attributes("-alpha", 1.0)

    def fade_out_tutorial(self):
        if not self.tut_win.winfo_exists(): return
        self.tut_alpha -= 0.15
        if self.tut_alpha > 0.0:
            self.tut_win.attributes("-alpha", self.tut_alpha)
            self.tut_win.after(20, self.fade_out_tutorial)
        else:
            self.tut_win.destroy()

    def build_main_frame(self):
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="NET IMMUNE", font=("Courier New", 22, "bold"), text_color=("#006688", "#00FFCC")).pack(side="left")
        ctk.CTkButton(top_frame, text="⚙️", width=30, height=30, fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), hover_color=("#AAAAAA", "#555555"), command=self.show_settings).pack(side="right")
        ctk.CTkButton(top_frame, text="❓", width=30, height=30, fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), hover_color=("#AAAAAA", "#555555"), command=self.show_tutorial_popup).pack(side="right", padx=5)

        self.create_agent_toggle(self.main_frame, "📋 Clipboard Watchdog", 1)
        self.create_agent_toggle(self.main_frame, "📁 Dropzone Scanner", 2)
        self.create_agent_toggle(self.main_frame, "🌐 Network Monitor", 3)
        self.create_agent_toggle(self.main_frame, "💾 USB / Drive Scanner", 4)
        self.create_agent_toggle(self.main_frame, "⚙️ Process Watchdog", 5)

        self.log_box = ctk.CTkTextbox(self.main_frame, height=120, font=("Courier New", 11), text_color=("#000000", "#00FFCC"), fg_color=("#E0E0E0", "#111111"))
        self.log_box.pack(pady=10, padx=15, fill="x")
        
        self.log_box.configure(state="normal")
        if self.mascot.session_history:
            for msg in self.mascot.session_history:
                self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        else:
            self.log_box.insert("end", "> System initialized...\n> Awaiting agent data...\n")
        self.log_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="EXPORT REPORT", fg_color="#0055AA", text_color="#FFFFFF", width=120, command=self.generate_report).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="POWER OFF", fg_color="#AA0000", text_color="#FFFFFF", width=120, command=self.full_shutdown).pack(side="right", padx=10)

    def build_settings_frame(self):
        top_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(top_frame, text="SETTINGS", font=("Courier New", 22, "bold"), text_color=("#006688", "#00FFCC")).pack(side="left")
        ctk.CTkButton(top_frame, text="⬅ Back", width=60, height=30, fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), command=self.show_main).pack(side="right")

        stat_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#E0E0E0", "#222222"))
        stat_frame.pack(pady=10, padx=15, fill="x")
        ctk.CTkLabel(stat_frame, text="📊 Threat Analytics", font=("Arial", 14, "bold"), text_color=("#000000", "#FFFFFF")).pack(pady=(10, 0))
        
        self.stat_filter_var = ctk.StringVar(value="All Time")
        self.stat_filter = ctk.CTkSegmentedButton(stat_frame, values=["Today", "This Month", "All Time"], variable=self.stat_filter_var, command=self.refresh_stats, selected_color="#0055AA")
        self.stat_filter.pack(pady=(5, 10))
        
        self.safe_label = ctk.CTkLabel(stat_frame, text="✅ Safe Items: 0", text_color=("#008800", "#00FFCC"), font=("Arial", 16, "bold"))
        self.safe_label.pack(pady=2)
        self.threat_label = ctk.CTkLabel(stat_frame, text="🚨 Threats Blocked: 0", text_color=("#CC0000", "#FF4444"), font=("Arial", 16, "bold"))
        self.threat_label.pack(pady=(0, 10))

        self.refresh_stats("All Time")

        theme_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#E0E0E0", "#222222"))
        theme_frame.pack(pady=10, padx=15, fill="x")
        ctk.CTkLabel(theme_frame, text="UI Theme", font=("Arial", 12), text_color=("#000000", "#FFFFFF")).pack(side="left", padx=10, pady=10)
        
        current_theme = load_data(CONFIG_FILE, {"theme": "dark"}).get("theme", "dark")
        self.theme_switch = ctk.CTkSwitch(theme_frame, text="Light/Dark", progress_color="#00FFCC", command=self.toggle_theme)
        if current_theme == "light": self.theme_switch.select()
        self.theme_switch.pack(side="right", padx=10)

        share_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        share_frame.pack(pady=10)
        
        ctk.CTkButton(share_frame, text="🔗 Share Net Immune", fg_color="#0055AA", text_color="#FFFFFF", hover_color="#0077CC", command=self.share_app).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(share_frame, text="ℹ️ About & Team", fg_color=("#666666", "#444444"), text_color="#FFFFFF", hover_color=("#444444", "#222222"), command=self.show_about_popup).grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkButton(self.settings_frame, text="🔥 Factory Reset (Wipe Data)", fg_color="transparent", border_width=1, border_color="#CC0000", text_color="#CC0000", hover_color="#550000", command=self.factory_reset).pack(side="bottom", pady=20)

    # --- UPGRADED FACTORY RESET ---
    def factory_reset(self):
        reset_win = ctk.CTkToplevel(self.window)
        reset_win.title("Factory Reset")
        reset_win.geometry("320x190")
        reset_win.transient(self.window) 
        reset_win.grab_set()             
        reset_win.focus_force()          
        reset_win.attributes("-topmost", True)
        reset_win.resizable(False, False)
        reset_win.configure(fg_color=("#F5F5F5", "#1E1E1E"))

        x = self.window.winfo_x() + 15
        y = self.window.winfo_y() + 200
        reset_win.geometry(f"+{x}+{y}")

        ctk.CTkLabel(reset_win, text="⚠️ WARNING", font=("Arial", 16, "bold"), text_color="#FF4444").pack(pady=(15, 5))
        ctk.CTkLabel(reset_win, text="This will permanently delete your API key, wipe all threat logs, and reset your statistics to zero. The app will then shut down.", font=("Arial", 11), text_color=("#000000", "#FFFFFF"), wraplength=280, justify="center").pack(padx=10, pady=5)

        def confirm_wipe():
            # 1. Delete Settings and Stats
            if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
            if os.path.exists(STATS_FILE): os.remove(STATS_FILE)
            
            # 2. Clear all internal agent logs
            if os.path.exists(LOGS_FOLDER):
                for file in os.listdir(LOGS_FOLDER):
                    try: os.remove(os.path.join(LOGS_FOLDER, file))
                    except: pass
            
            # 3. Clear all old scanned files from the Dropzone
            if os.path.exists(WATCH_FOLDER):
                for file in os.listdir(WATCH_FOLDER):
                    try: os.remove(os.path.join(WATCH_FOLDER, file))
                    except: pass
                    
            # 4. Delete the generated PDF/TXT reports sitting in the main folder
            for report_file in ["Net_Immune_Master_Report.pdf", "Net_Immune_Master_Report.txt"]:
                if os.path.exists(report_file):
                    try: os.remove(report_file)
                    except: pass
            
            # 5. Restart application to clean state
            reboot_app() 

        btn_frame = ctk.CTkFrame(reset_win, fg_color="transparent")
        btn_frame.pack(pady=(10, 0))
        ctk.CTkButton(btn_frame, text="Cancel", width=100, fg_color=("#888888", "#555555"), text_color="#FFFFFF", command=reset_win.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="WIPE DATA", width=100, fg_color="#CC0000", text_color="#FFFFFF", hover_color="#FF0000", command=confirm_wipe).pack(side="right", padx=10)

    def refresh_stats(self, filter_choice):
        stats = load_data(STATS_FILE, {"all_time": {"safe": 0, "threats": 0}, "history": {}})
        if "safe" in stats and isinstance(stats["safe"], int):
            stats = {"all_time": {"safe": stats.get("safe", 0), "threats": stats.get("threats", 0)}, "history": {}}

        safe_count, threat_count = 0, 0
        
        if filter_choice == "All Time":
            safe_count = stats.get("all_time", {}).get("safe", 0)
            threat_count = stats.get("all_time", {}).get("threats", 0)
        elif filter_choice == "Today":
            today = time.strftime("%Y-%m-%d")
            safe_count = stats.get("history", {}).get(today, {}).get("safe", 0)
            threat_count = stats.get("history", {}).get(today, {}).get("threats", 0)
        elif filter_choice == "This Month":
            current_month = time.strftime("%Y-%m")
            for date_key, daily_data in stats.get("history", {}).items():
                if str(date_key).startswith(current_month):
                    safe_count += daily_data.get("safe", 0)
                    threat_count += daily_data.get("threats", 0)

        self.safe_label.configure(text=f"✅ Safe Items: {safe_count}")
        self.threat_label.configure(text=f"🚨 Threats Blocked: {threat_count}")

    def show_about_popup(self):
        about_win = ctk.CTkToplevel(self.window)
        about_win.title("About Net Immune")
        about_win.geometry("300x340")
        about_win.transient(self.window) 
        about_win.grab_set()             
        about_win.focus_force()          
        about_win.attributes("-topmost", True)
        about_win.resizable(False, False)
        about_win.configure(fg_color=("#F0F0F0", "#181818"))

        x = self.window.winfo_x() + 25
        y = self.window.winfo_y() + 100
        about_win.geometry(f"+{x}+{y}")

        ctk.CTkLabel(about_win, text="NET IMMUNE", font=("Courier New", 20, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(15, 0))
        ctk.CTkLabel(about_win, text="v1.0 Core | Llama-3 AI Engine", font=("Arial", 10), text_color=("#555555", "#888888")).pack(pady=(0, 15))
        ctk.CTkLabel(about_win, text="Developed By:", font=("Arial", 14, "bold"), text_color=("#000000", "#FFFFFF")).pack(pady=(5, 5))

        team_frame = ctk.CTkFrame(about_win, fg_color=("#E0E0E0", "#222222"), corner_radius=10)
        team_frame.pack(padx=20, fill="x")

        team_members = ["Kamalesh S", "John Peter V", "Junaid Ahmed J", "Lingesh M"]
        for member in team_members:
            ctk.CTkLabel(team_frame, text=f"👨‍💻 {member}", font=("Arial", 13, "bold"), text_color=("#333333", "#CCCCCC"), anchor="w").pack(padx=15, pady=4, fill="x")

        ctk.CTkButton(about_win, text="Close", fg_color="transparent", border_width=1, border_color=("#AA0000", "#FF4444"), text_color=("#AA0000", "#FF4444"), hover_color=("#FFCCCC", "#550000"), command=about_win.destroy).pack(pady=(20, 10))

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)

    def show_main(self):
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def share_app(self):
        share_win = ctk.CTkToplevel(self.window)
        share_win.title("Share Net Immune")
        share_win.geometry("280x350")
        share_win.transient(self.window) 
        share_win.grab_set()             
        share_win.focus_force()          
        share_win.attributes("-topmost", True)
        share_win.resizable(False, False)
        share_win.configure(fg_color=("#F0F0F0", "#181818"))

        x = self.window.winfo_x() + 35
        y = self.window.winfo_y() + 100
        share_win.geometry(f"+{x}+{y}")

        repo_link = "https://github.com/Kamalesh-S2k5-RR/Net_Immune.git" 
        promo_text = "Check out Net Immune! I built an AI-powered cybersecurity agent that scans for hackers in real-time. 🤖🛡️"
        
        safe_text = urllib.parse.quote(promo_text)
        safe_link = urllib.parse.quote(repo_link)

        def copy_to_clipboard():
            pyperclip.copy(repo_link)
            self.add_log_text("> GitHub Link copied!")
            send_alert("Link Copied", "GitHub link copied to your clipboard!")

        ctk.CTkLabel(share_win, text="Share Project", font=("Courier New", 18, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(15, 10))
        ctk.CTkButton(share_win, text="⬛ Open in GitHub", fg_color=("#333333", "#333333"), text_color=("#FFFFFF", "#FFFFFF"), hover_color=("#555555", "#555555"), command=lambda: webbrowser.open(repo_link)).pack(pady=5)
        ctk.CTkButton(share_win, text="📄 Copy Link", fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), hover_color=("#AAAAAA", "#555555"), command=copy_to_clipboard).pack(pady=5)
        ctk.CTkButton(share_win, text="💬 Share on WhatsApp", fg_color="#25D366", text_color="#FFFFFF", hover_color="#128C7E", command=lambda: webbrowser.open(f"https://api.whatsapp.com/send?text={safe_text}%20{safe_link}")).pack(pady=5)
        ctk.CTkButton(share_win, text="✈️ Share on Telegram", fg_color="#0088cc", text_color="#FFFFFF", hover_color="#005580", command=lambda: webbrowser.open(f"https://t.me/share/url?url={safe_link}&text={safe_text}")).pack(pady=5)
        ctk.CTkButton(share_win, text="🐦 Share on X (Twitter)", fg_color="#1DA1F2", text_color="#FFFFFF", hover_color="#0C85D0", command=lambda: webbrowser.open(f"https://twitter.com/intent/tweet?text={safe_text}&url={safe_link}")).pack(pady=5)
        ctk.CTkButton(share_win, text="Close", fg_color="transparent", border_width=1, border_color=("#AA0000", "#FF4444"), text_color=("#AA0000", "#FF4444"), hover_color=("#FFCCCC", "#550000"), command=share_win.destroy).pack(pady=(15, 5))

    def toggle_theme(self):
        self.theme_switch.configure(state="disabled") 
        self.fade_step = 1.0 
        self.fade_out()

    def fade_out(self):
        self.fade_step -= 0.15 
        if self.fade_step > 0.0:
            self.window.attributes("-alpha", self.fade_step)
            self.window.after(20, self.fade_out) 
        else:
            self.window.attributes("-alpha", 0.0) 
            self._execute_theme_change() 

    def _execute_theme_change(self):
        new_theme = "light" if self.theme_switch.get() == 1 else "dark"
        ctk.set_appearance_mode(new_theme)
        config = load_data(CONFIG_FILE, {})
        config["theme"] = new_theme
        save_data(CONFIG_FILE, config)
        self.window.after(50, self.fade_in) 

    def fade_in(self):
        self.fade_step += 0.15 
        if self.fade_step < 1.0:
            self.window.attributes("-alpha", self.fade_step)
            self.window.after(20, self.fade_in) 
        else:
            self.window.attributes("-alpha", 1.0) 
            self.theme_switch.configure(state="normal") 

    def create_agent_toggle(self, parent, text, agent_num):
        frame = ctk.CTkFrame(parent, fg_color=("#E0E0E0", "#222222"))
        frame.pack(pady=3, padx=15, fill="x")
        ctk.CTkLabel(frame, text=text, font=("Arial", 12), text_color=("#000000", "#FFFFFF")).pack(side="left", padx=10, pady=8)
        
        is_on = getattr(self.mascot, f"agent{agent_num}_on")
        switch_var = ctk.IntVar(value=1 if is_on else 0)
        
        switch = ctk.CTkSwitch(frame, text="", progress_color="#00FFCC", variable=switch_var, command=lambda: self.toggle_agent(agent_num, switch_var.get()))
        switch.pack(side="right", padx=10)

    def toggle_agent(self, agent_num, state):
        setattr(self.mascot, f"agent{agent_num}_on", bool(state))
        self.mascot.log_to_dashboard(f"> Agent {agent_num} set to: {'ON' if state else 'OFF'}")

    def add_log_text(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end") 
        self.log_box.configure(state="disabled")

    def generate_report(self):
        try:
            from fpdf import FPDF
        except ImportError:
            tkinter.messagebox.showerror("Missing Library", "PDF Engine not found!\n\nPlease open your VS Code terminal and type:\npip install fpdf\n\nThen try exporting again.")
            return

        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 22)
                self.set_text_color(0, 102, 204) 
                self.cell(0, 10, 'NET IMMUNE', 0, 1, 'C')
                self.set_font('Arial', 'B', 12)
                self.set_text_color(100, 100, 100) 
                self.cell(0, 8, 'ENTERPRISE SECURITY AUDIT', 0, 1, 'C')
                self.set_draw_color(0, 102, 204)
                self.line(10, 30, 200, 30) 
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 10, f"Report Generated: {current_time}", 0, 1, 'R')
        pdf.ln(5)

        agents = ["clipboard", "folder", "network", "usb", "process"]
        agent_names_safe = {
            "clipboard": "CLIPBOARD WATCHDOG",
            "folder": "DROPZONE SCANNER",
            "network": "NETWORK MONITOR",
            "usb": "USB / DRIVE SCANNER",
            "process": "PROCESS WATCHDOG"
        }

        for agent in agents:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(255, 255, 255) 
            pdf.set_fill_color(20, 30, 48)    
            pdf.cell(0, 10, f"  {agent_names_safe[agent]}", 0, 1, 'L', fill=True)
            pdf.ln(4)

            log_file = os.path.join(LOGS_FOLDER, f"{agent}_log.txt")

            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as lf:
                    lines = lf.readlines()[-15:] 
                    if not lines:
                        pdf.set_font("Arial", 'I', 10)
                        pdf.set_text_color(150, 150, 150)
                        pdf.cell(0, 8, "No threats or events logged yet.", 0, 1)
                        pdf.ln(4)
                        continue
                    
                    for line in reversed(lines):
                        clean_line = line.encode('ascii', 'ignore').decode('ascii').strip()
                        if not clean_line: continue
                        
                        if clean_line.startswith("[") and "] " in clean_line:
                            parts = clean_line.split("] ", 1)
                            timestamp = parts[0] + "]"
                            rest = parts[1]
                            
                            if " | Result: " in rest:
                                data_part, result_part = rest.rsplit(" | Result: ", 1)
                            else:
                                data_part = rest
                                result_part = ""
                                
                            pdf.set_font("Arial", 'B', 10)
                            pdf.set_text_color(100, 100, 150) 
                            pdf.cell(0, 6, timestamp, 0, 1)
                            
                            pdf.set_font("Arial", '', 10)
                            pdf.set_text_color(60, 60, 60)
                            pdf.multi_cell(0, 5, f"Data: {data_part}")
                            
                            if result_part:
                                if "[SAFE]" in result_part:
                                    pdf.set_text_color(0, 128, 0) 
                                elif "Threat" in result_part or "[SUSPICIOUS]" in result_part or "[MALICIOUS]" in result_part:
                                    pdf.set_text_color(200, 0, 0) 
                                elif "[ERROR]" in result_part:
                                    pdf.set_text_color(200, 100, 0) 
                                else:
                                    pdf.set_text_color(50, 50, 50)
                                    
                                pdf.set_font("Arial", 'B', 10)
                                pdf.multi_cell(0, 5, f"Verdict: {result_part}")
                            
                            pdf.ln(2)
                            pdf.set_draw_color(230, 230, 230)
                            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                            pdf.ln(2)
                        else:
                            pdf.set_font("Arial", '', 10)
                            pdf.set_text_color(100, 100, 100)
                            pdf.multi_cell(0, 6, clean_line)
                            pdf.ln(2)
            else:
                pdf.set_font("Arial", 'I', 10)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 8, "No log file found for this agent.", 0, 1)
                
            pdf.ln(6) 

        report_path = "Net_Immune_Master_Report.pdf"
        try:
            pdf.output(report_path)
            os.startfile(report_path)
        except Exception as e:
            tkinter.messagebox.showerror("PDF Export Error", f"Failed to open PDF. Ensure it isn't currently open in another program.\n\nError: {e}")

    def close_window(self):
        self.mascot.dashboard_open = False
        self.window.destroy()

    def full_shutdown(self):
        send_alert("Net Immune Offline", "All security agents have been disabled.")
        self.mascot.running = False
        os._exit(0)

# --- MASCOT ENGINE ---
class FloatingMascot:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True) 
        self.root.attributes("-topmost", True) 
        
        transparent_color = "#000001"
        self.root.config(bg=transparent_color)
        self.root.wm_attributes("-transparentcolor", transparent_color)

        try: self.mascot_img = ImageTk.PhotoImage(Image.open(resource_path("mascot.png")).resize((100, 100)))
        except: self.root.destroy(); return
        try: self.greet_img = ImageTk.PhotoImage(Image.open(resource_path("mascot_greet.png")).resize((100, 100)))
        except: self.greet_img = None 
        try: self.alert_img = ImageTk.PhotoImage(Image.open(resource_path("mascot_alert.png")).resize((100, 100)))
        except: self.alert_img = None 

        self.label = tk.Label(self.root, image=self.mascot_img, bg=transparent_color)
        self.label.pack()

        self.dragged = False

        self.label.bind("<Enter>", lambda e: self.root.geometry(f"+{self.root.winfo_x()}+{self.root.winfo_y() - 5}"))
        self.label.bind("<Leave>", lambda e: self.root.geometry(f"+{self.root.winfo_x()}+{self.root.winfo_y() + 5}"))
        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.do_drag)
        self.label.bind("<ButtonRelease-1>", self.on_click_release)

        self.dashboard_open = False
        self.dashboard_ref = None
        
        self.session_history = [] 
        
        self.agent1_on, self.agent2_on, self.agent3_on, self.agent4_on, self.agent5_on = True, True, True, True, True

        self.running = True
        threading.Thread(target=self.ai_background_loop, daemon=True).start()

    def trigger_alert_emotion(self):
        if self.alert_img:
            self.label.configure(image=self.alert_img)
            self.root.after(4000, lambda: self.label.configure(image=self.mascot_img)) 

    def start_drag(self, event):
        self.x, self.y, self.dragged = event.x, event.y, False 

    def do_drag(self, event):
        self.dragged = True
        new_x, new_y = self.root.winfo_pointerx() - self.x, self.root.winfo_pointery() - self.y
        self.root.geometry(f"+{new_x}+{new_y}")
        if self.dashboard_open and self.dashboard_ref: self.dashboard_ref.window.geometry(f"+{new_x - 125}+{new_y + 110}")

    def on_click_release(self, event):
        if not self.dragged:
            if self.greet_img:
                self.label.configure(image=self.greet_img)
                self.root.after(1000, lambda: self.label.configure(image=self.mascot_img))
            if self.dashboard_open and self.dashboard_ref: self.dashboard_ref.close_window()
            else:
                self.dashboard_open = True
                self.dashboard_ref = DashboardWindow(self)

    def log_to_dashboard(self, message):
        print(message) 
        self.session_history.append(message)
        if len(self.session_history) > 30: 
            self.session_history.pop(0)
            
        if self.dashboard_open and self.dashboard_ref: 
            self.root.after(0, self.dashboard_ref.add_log_text, message)

    def ai_background_loop(self):
        self.log_to_dashboard("> System Initialized...")
        send_alert("Net Immune Online", "Click the mascot to view the dashboard.")
        
        try:
            previous_clipboard = pyperclip.paste()
        except Exception:
            previous_clipboard = ""
            
        network_timer, process_timer = 0, 0
        known_drives = [p.device for p in psutil.disk_partitions() if 'removable' in p.opts.lower() or 'cdrom' not in p.opts.lower()]
        
        while self.running:
            # --- AGENT 1: CLIPBOARD ---
            if self.agent1_on:
                try:
                    curr_clip = pyperclip.paste()
                    if curr_clip != previous_clipboard and len(curr_clip) > 5:
                        self.log_to_dashboard("\n[Clipboard Agent] Scanning...")
                        res = analyze_threat("clipboard", curr_clip)
                        clean_msg = res.split("] ")[-1] if "] " in res else res
                        write_to_log("clipboard", f"Text: {curr_clip[:30]}... | Result: {res}")
                        
                        if "[ERROR]" in res.upper():
                            self.log_to_dashboard(f"⚠️ {clean_msg}")
                        elif "[SAFE]" not in res.upper():
                            self.root.after(0, self.trigger_alert_emotion)
                            send_alert("⚠️ Clipboard Threat!", clean_msg)
                            self.log_to_dashboard(res)
                        else:
                            send_alert("✅ Safe Text", clean_msg)
                            self.log_to_dashboard(res)
                            
                        previous_clipboard = curr_clip
                except Exception:
                    pass

            # --- AGENT 2: FOLDER DROPZONE ---
            if self.agent2_on:
                for filename in os.listdir(WATCH_FOLDER):
                    if not filename.endswith(".scanned"):
                        filepath = os.path.join(WATCH_FOLDER, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as file: res = analyze_threat("file", f"Filename: {filename}\nContent:\n{file.read()}")
                            clean_msg = res.split("] ")[-1] if "] " in res else res
                            write_to_log("folder", f"File: {filename} | Result: {res}")
                            
                            if "[ERROR]" in res.upper():
                                self.log_to_dashboard(f"⚠️ {clean_msg}")
                            elif "[SAFE]" not in res.upper():
                                self.root.after(0, self.trigger_alert_emotion)
                                send_alert("🚨 Malicious File!", clean_msg)
                                self.log_to_dashboard(res)
                            else:
                                send_alert("✅ Safe File", clean_msg)
                                self.log_to_dashboard(res)
                                
                            os.replace(filepath, filepath + ".scanned")
                        except: pass

            # --- AGENT 3: NETWORK (Scans every 60 seconds) ---
            if self.agent3_on:
                network_timer += 1
                if network_timer >= 60: 
                    try:
                        net_out = subprocess.check_output("netstat -n | findstr ESTABLISHED", shell=True, text=True)
                        short_net = "\n".join(net_out.strip().split("\n")[:10])
                        if short_net:
                            res = analyze_threat("network", short_net)
                            clean_msg = res.split("] ")[-1] if "] " in res else res
                            
                            if "[ERROR]" in res.upper():
                                self.log_to_dashboard(f"⚠️ {clean_msg}")
                            elif "[SAFE]" not in res.upper():
                                self.root.after(0, self.trigger_alert_emotion)
                                send_alert("🌐 Network Threat!", clean_msg)
                                self.log_to_dashboard(res)
                            else:
                                self.log_to_dashboard("✅ NETWORK: Traffic secure.")
                    except: pass
                    network_timer = 0

            # --- AGENT 4: USB DRIVE SCANNER ---
            if self.agent4_on:
                try:
                    current_drives = [p.device for p in psutil.disk_partitions() if 'removable' in p.opts.lower() or 'cdrom' not in p.opts.lower()]
                    new_drives = [d for d in current_drives if d not in known_drives]
                    
                    for drive in new_drives:
                        self.log_to_dashboard(f"\n[USB Agent] New drive detected: {drive}")
                        
                        try:
                            time.sleep(1.5) 
                            usage = psutil.disk_usage(drive)
                            total_gb = round(usage.total / (1024**3), 2)
                            used_gb = round(usage.used / (1024**3), 2)
                            free_gb = round(usage.free / (1024**3), 2)
                            storage_info = f"[{total_gb}GB Total | {used_gb}GB Used | {free_gb}GB Free]"
                            
                            all_items = os.listdir(drive)
                            files = [f for f in all_items if os.path.isfile(os.path.join(drive, f))]
                            folders = [f for f in all_items if os.path.isdir(os.path.join(drive, f))]
                            
                            drive_contents = (files + folders)[:50] 
                            content_str = ", ".join(drive_contents) if drive_contents else "Empty Drive"
                            
                        except Exception:
                            storage_info = "[Storage Info Unavailable]"
                            content_str = "Could not read contents"
                            
                        self.log_to_dashboard(f"> Details: {storage_info}")
                        payload = f"A new USB drive was mounted at {drive}.\nCapacity: {storage_info}\nRoot Directory Contents: {content_str}"
                        res = analyze_threat("usb", payload)
                        clean_msg = res.split("] ")[-1] if "] " in res else res
                        write_to_log("usb", f"Drive: {drive} | {storage_info} | Result: {res}")
                        
                        if "[ERROR]" in res.upper():
                            self.log_to_dashboard(f"⚠️ {clean_msg}")
                        elif "[SAFE]" not in res.upper():
                            self.root.after(0, self.trigger_alert_emotion)
                            send_alert("💾 Suspicious USB Detected!", clean_msg)
                            self.log_to_dashboard(res)
                        else:
                            send_alert("✅ USB Drive Safe", clean_msg)
                            self.log_to_dashboard(res)
                            
                    known_drives = current_drives
                except Exception: pass
                
            # --- AGENT 5: PROCESS WATCHDOG (Scans every 5 minutes / 300 seconds) ---
            if self.agent5_on:
                process_timer += 1
                if process_timer >= 300:
                    self.log_to_dashboard("\n[Process Agent] Auditing RAM...")
                    try:
                        procs = []
                        for p in psutil.process_iter(['name', 'cpu_percent']):
                            try:
                                if p.info['cpu_percent'] is not None and p.info['cpu_percent'] > 1.0:
                                    procs.append((p.info['name'], p.info['cpu_percent']))
                            except: pass
                            
                        procs = sorted(procs, key=lambda x: x[1], reverse=True)[:10]
                        
                        if procs:
                            proc_str = "\n".join([f"Process: {n} | CPU Usage: {c}%" for n, c in procs])
                            res = analyze_threat("process", proc_str)
                            clean_msg = res.split("] ")[-1] if "] " in res else res
                            write_to_log("process", f"Top Process: {procs[0][0]} | Result: {res}")
                            
                            if "[ERROR]" in res.upper():
                                self.log_to_dashboard(f"⚠️ {clean_msg}")
                            elif "[SAFE]" not in res.upper():
                                self.root.after(0, self.trigger_alert_emotion)
                                send_alert("⚙️ Suspicious Process!", clean_msg)
                                self.log_to_dashboard(res)
                            else:
                                self.log_to_dashboard("✅ PROCESS: Memory secure.")
                    except: pass
                    process_timer = 0
            
            time.sleep(1) 

def start_main_app():
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('netimmune.core.app.1') 
    except: pass

    config = load_data(CONFIG_FILE, {"theme": "dark"})
    ctk.set_appearance_mode(config.get("theme", "dark"))
    ctk.set_default_color_theme("green")

    root = tk.Tk()
    try: root.iconphoto(False, tk.PhotoImage(file=resource_path("mascot.png")))
    except: pass
    
    root.geometry(f"100x100+{(root.winfo_screenwidth() // 2) - 50}+20")
    app = FloatingMascot(root)
    root.mainloop()

if __name__ == "__main__":
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, "NetImmune_App_Mutex")
    if ctypes.windll.kernel32.GetLastError() == 183: 
        error_root = tk.Tk()
        error_root.withdraw()
        tkinter.messagebox.showerror("Net Immune", "⚠️ Net Immune is already running!\n\nPlease check your screen or taskbar for the floating bot.")
        os._exit(0)

    config_data = load_data(CONFIG_FILE, {})
    if not config_data.get("api_key"):
        ctk.set_appearance_mode("dark")
        wizard = SetupWizard()
        wizard.root.mainloop()
    else:
        start_main_app()