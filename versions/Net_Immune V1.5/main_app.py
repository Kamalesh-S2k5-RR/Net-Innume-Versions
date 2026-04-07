import tkinter as tk
from tkinter import filedialog
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
import shutil
import re
import winreg
from groq import Groq
from plyer import notification
import keyboard

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# --- FILE PATHS & CONFIGURATION ---
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')
LOGS_FOLDER = "Logs"
WATCH_FOLDER = "Threat_Dropzone"
CONFIG_FILE = "config.json"
STATS_FILE = "stats.json"

for folder in [LOGS_FOLDER, WATCH_FOLDER]:
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
        icon_path = os.path.abspath(resource_path("assets/mascot.ico"))
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
    elif prompt_type == "file": sys_prompt = "Analyze this downloaded file name AND its internal text headers. Look for malware signatures, obfuscated code, or hacking tools. If it's a known safe tool with a weird name, mark it SAFE. Categorize exactly as [UNSAFE_PIRACY], [MALWARE], or [SAFE]. Format exactly: [TAG] Reason."
    elif prompt_type == "manual_file": sys_prompt = "Analyze this manually uploaded file name AND its internal text headers. Look for malicious intent, double extensions, or script types. Categorize exactly: [SAFE], [MALWARE], [UNSAFE_PIRACY]. Format exactly: [TAG] Reason."
    elif prompt_type == "web": sys_prompt = "Analyze this active window title. Is the user on a dangerous, cracked, phishing, torrent, or illegal software site? Categorize exactly: [SAFE], [UNSAFE_WEB]. Format exactly: [TAG] Reason."
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
            self.root.iconbitmap(resource_path("assets/mascot.ico"))
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
        self.window.geometry("350x540") 
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)
        self.window.configure(fg_color=("#F0F0F0", "#181818"))

        try:
            self.window.iconbitmap(resource_path("assets/mascot.ico"))
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
        self.tut_win.geometry("380x440+-10000+-10000")
        self.tut_win.attributes("-alpha", 0.0) 
        
        self.tut_win.transient(self.window) 
        self.tut_win.grab_set()             
        self.tut_win.focus_force()          
        self.tut_win.attributes("-topmost", True)
        self.tut_win.resizable(False, False)
        self.tut_win.configure(fg_color=("#F5F5F5", "#1E1E1E"))

        ctk.CTkLabel(self.tut_win, text="Welcome to Net Immune!", font=("Courier New", 18, "bold"), text_color=("#006688", "#00FFCC")).pack(pady=(15, 2))
        ctk.CTkLabel(self.tut_win, text="Your AI-Powered Cybersecurity Shield", font=("Arial", 12, "italic"), text_color=("#555555", "#AAAAAA")).pack(pady=(0, 10))
        
        guide_frame = ctk.CTkFrame(self.tut_win, fg_color=("#E0E0E0", "#2A2A2A"), corner_radius=10)
        guide_frame.pack(padx=20, pady=5, fill="x")

        agents = [
            ("⚡ Hotkey:", "Highlight text and press ` (Backtick) to scan."),
            ("📂 UI Dropzone:", "Click the sleek button to manually scan files."),
            ("📥 Downloads:", "Auto-scans new files in your downloads folder."),
            ("🌐 Web Monitor:", "Warns you of cracked or phishing sites on Browsers."),
            ("💾 USB Drive:", "Auto-scans external drives on insertion."),
            ("⚙️ Process:", "Watches RAM for suspicious activity.")
        ]

        for icon_title, desc in agents:
            row_frame = ctk.CTkFrame(guide_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=4)
            ctk.CTkLabel(row_frame, text=icon_title, font=("Arial", 11, "bold"), text_color=("#000000", "#FFFFFF"), width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=desc, font=("Arial", 10), text_color=("#333333", "#CCCCCC"), anchor="w", wraplength=220).pack(side="left", fill="x", expand=True)

        pro_tip = "🚨 Pro Tip: If the floating bot turns RED, a threat was blocked!"
        ctk.CTkLabel(self.tut_win, text=pro_tip, font=("Arial", 12, "bold"), text_color=("#CC0000", "#FF6666"), wraplength=340, justify="center").pack(pady=(10, 5), padx=10)
        
        ctk.CTkButton(self.tut_win, text="Got it! Secure my system", font=("Arial", 14, "bold"), fg_color="#00AA55", text_color="#FFFFFF", hover_color="#00CC66", command=self.fade_out_tutorial).pack(pady=(5, 15))

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
        top_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(top_frame, text="NET IMMUNE", font=("Courier New", 22, "bold"), text_color=("#006688", "#00FFCC")).pack(side="left")
        ctk.CTkButton(top_frame, text="⚙️", width=30, height=30, fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), hover_color=("#AAAAAA", "#555555"), command=self.show_settings).pack(side="right")
        ctk.CTkButton(top_frame, text="❓", width=30, height=30, fg_color=("#CCCCCC", "#333333"), text_color=("#000000", "#FFFFFF"), hover_color=("#AAAAAA", "#555555"), command=self.show_tutorial_popup).pack(side="right", padx=5)

        self.create_agent_toggle(self.main_frame, "⚡ Hotkey Scanner ( ` )", 1)
        self.create_agent_toggle(self.main_frame, "📂 UI Dropzone Scanner", 2)
        self.create_agent_toggle(self.main_frame, "📥 Downloads Watchdog", 3)
        self.create_agent_toggle(self.main_frame, "🌐 Active Web Monitor", 4)
        self.create_agent_toggle(self.main_frame, "💾 USB / Drive Scanner", 5)
        self.create_agent_toggle(self.main_frame, "⚙️ Process / Net Watchdog", 6)

        drop_btn = ctk.CTkButton(
            self.main_frame, 
            text="📁 SELECT FILE TO UPLOAD", 
            font=("Arial", 12, "bold"), 
            text_color="#FFFFFF", 
            fg_color="#0055AA", 
            hover_color="#004488", 
            height=30, 
            corner_radius=15,           
            border_width=2,             
            border_color="#00FFCC",     
            command=self.manual_file_scan
        )
        drop_btn.pack(pady=(5, 5), padx=25, fill="x")

        self.log_box = ctk.CTkTextbox(self.main_frame, height=60, font=("Courier New", 10), text_color=("#000000", "#00FFCC"), fg_color=("#E0E0E0", "#111111"))
        self.log_box.pack(pady=0, padx=15, fill="both", expand=True)
        
        self.log_box.configure(state="normal")
        if self.mascot.session_history:
            for msg in self.mascot.session_history:
                self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        else:
            self.log_box.insert("end", "> System initialized...\n")
        self.log_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=(5, 10))
        ctk.CTkButton(btn_frame, text="EXPORT REPORT", fg_color="#0055AA", text_color="#FFFFFF", width=120, command=self.generate_report).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="POWER OFF", fg_color="#AA0000", text_color="#FFFFFF", width=120, command=self.full_shutdown).pack(side="right", padx=10)

    def manual_file_scan(self):
        if not getattr(self.mascot, "agent2_on"):
            tkinter.messagebox.showwarning("Agent Disabled", "Please enable the 'UI Dropzone Scanner' agent first.")
            return

        file_path = filedialog.askopenfilename(title="Select File to Scan")
        if file_path:
            filename = os.path.basename(file_path)
            self.add_log_text(f"\n[UI Dropzone] Copying & Scanning: {filename}...")
            
            def run_scan():
                try:
                    dest_path = os.path.join(WATCH_FOLDER, filename + ".scanned")
                    shutil.copy2(file_path, dest_path)
                    
                    try:
                        file_size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                        if file_size_mb > 15.0:
                            content_peek = f"[File too large ({round(file_size_mb, 1)} MB). Analyzed filename only.]"
                        else:
                            with open(dest_path, 'rb') as f:
                                content_peek = f.read(2048).decode('utf-8', errors='ignore')
                    except:
                        content_peek = "[Unreadable Binary]"
                except Exception as e:
                    content_peek = "[Error Reading File]"

                payload = f"Filename: {filename}\nInternal File Code/Headers: {content_peek}"
                res = analyze_threat("manual_file", payload)
                
                clean_msg = res.split("] ")[-1] if "] " in res else res
                write_to_log("folder", f"Manual File: {filename} | Result: {res}")
                
                if "[ERROR]" in res.upper():
                    self.mascot.log_to_dashboard(f"⚠️ {clean_msg}")
                elif "[SAFE]" not in res.upper():
                    self.mascot.root.after(0, self.mascot.trigger_alert_emotion)
                    send_alert("🚨 Malicious File Detected!", clean_msg)
                    self.mascot.log_to_dashboard(res)
                else:
                    send_alert("✅ File is Safe", clean_msg)
                    self.mascot.log_to_dashboard(res)
                    
            threading.Thread(target=run_scan, daemon=True).start()

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

        # --- AUTO-START FRAME ---
        startup_frame = ctk.CTkFrame(self.settings_frame, fg_color=("#E0E0E0", "#222222"))
        startup_frame.pack(pady=10, padx=15, fill="x")
        ctk.CTkLabel(startup_frame, text="Auto-Start with Windows", font=("Arial", 12), text_color=("#000000", "#FFFFFF")).pack(side="left", padx=10, pady=10)
        
        self.startup_switch = ctk.CTkSwitch(startup_frame, text="ON/OFF", progress_color="#00FFCC", command=self.toggle_startup)
        if self.is_autostart_enabled():
            self.startup_switch.select()
        self.startup_switch.pack(side="right", padx=10)
        # ------------------------

        share_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        share_frame.pack(pady=10)
        
        ctk.CTkButton(share_frame, text="🔗 Share Net Immune", fg_color="#0055AA", text_color="#FFFFFF", hover_color="#0077CC", command=self.share_app).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(share_frame, text="ℹ️ About & Team", fg_color=("#666666", "#444444"), text_color="#FFFFFF", hover_color=("#444444", "#222222"), command=self.show_about_popup).grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkButton(self.settings_frame, text="🔥 Factory Reset (Wipe Data)", fg_color="transparent", border_width=1, border_color="#CC0000", text_color="#CC0000", hover_color="#550000", command=self.factory_reset).pack(side="bottom", pady=20)

    # --- NEW REGISTRY LOGIC FOR AUTO-START ---
    def is_autostart_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "NetImmune")
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def toggle_startup(self):
        enable = self.startup_switch.get() == 1
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "NetImmune"
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        vbs_path = os.path.join(base_dir, "Start_Net_Immune.vbs")
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'wscript.exe "{vbs_path}"')
                self.mascot.log_to_dashboard("> Auto-Start Enabled.")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    self.mascot.log_to_dashboard("> Auto-Start Disabled.")
                except FileNotFoundError: pass
            winreg.CloseKey(key)
        except Exception as e:
            self.mascot.log_to_dashboard(f"> [Error] Auto-Start toggle failed: {e}")

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
            if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
            if os.path.exists(STATS_FILE): os.remove(STATS_FILE)
            
            if os.path.exists(LOGS_FOLDER):
                for file in os.listdir(LOGS_FOLDER):
                    try: os.remove(os.path.join(LOGS_FOLDER, file))
                    except: pass
            
            if os.path.exists(WATCH_FOLDER):
                for file in os.listdir(WATCH_FOLDER):
                    try: os.remove(os.path.join(WATCH_FOLDER, file))
                    except: pass
                    
            for report_file in ["Net_Immune_Master_Report.pdf", "Net_Immune_Master_Report.txt"]:
                if os.path.exists(report_file):
                    try: os.remove(report_file)
                    except: pass
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
        ctk.CTkLabel(about_win, text="v1.5 Core | Llama-3 AI Engine", font=("Arial", 10), text_color=("#555555", "#888888")).pack(pady=(0, 15))
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

        repo_link = "https://github.com/Kamalesh-S2k5-RR/Net_Immune_final_code.git" 
        promo_text = "Check out Net Immune! I built an AI-powered cybersecurity agent that scans for hackers in real-time. 🤖🛡️"
        
        safe_text = urllib.parse.quote(promo_text)
        safe_link = urllib.parse.quote(repo_link)

        def copy_to_clipboard():
            pyperclip.copy(repo_link)
            self.add_log_text("> Download Link copied!")
            send_alert("Link Copied", "Download link copied to your clipboard!")

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
        frame.pack(pady=1, padx=15, fill="x")
        ctk.CTkLabel(frame, text=text, font=("Arial", 12), text_color=("#000000", "#FFFFFF")).pack(side="left", padx=10, pady=2)
        
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

    # --- UPGRADED PDF ENGINE WITH USB HARDWARE EXCEPTION ---
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
                self.set_text_color(200, 0, 0) 
                self.cell(0, 8, 'INCIDENT & THREAT AUDIT', 0, 1, 'C')
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

        stats = load_data(STATS_FILE, {"all_time": {"safe": 0, "threats": 0}, "history": {}})
        total_safe = stats.get("all_time", {}).get("safe", 0)
        total_threats = stats.get("all_time", {}).get("threats", 0)
        total_scanned = total_safe + total_threats

        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "EXECUTIVE SUMMARY", 0, 1, 'L')
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, f"Total Items Scanned by AI: {total_scanned}", 0, 1, 'L')
        pdf.set_font("Arial", 'B', 11)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 6, f"Active Threats Blocked / Flagged: {total_threats}", 0, 1, 'L')
        pdf.ln(10)

        agents = ["clipboard", "folder", "network", "usb", "process"]
        agent_names_safe = {
            "clipboard": "HOTKEY / CLIPBOARD WATCHDOG",
            "folder": "DOWNLOADS & UI DROPZONE",
            "network": "ACTIVE WEB MONITOR",
            "usb": "USB / DRIVE SCANNER",
            "process": "PROCESS WATCHDOG"
        }

        for agent in agents:
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(255, 255, 255) 
            pdf.set_fill_color(20, 30, 48)    
            pdf.cell(0, 8, f"  {agent_names_safe[agent]}", 0, 1, 'L', fill=True)
            pdf.ln(4)

            log_file = os.path.join(LOGS_FOLDER, f"{agent}_log.txt")
            logs_printed = False

            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as lf:
                    lines = lf.readlines()[-30:] 
                    
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
                            
                            is_safe = "[SAFE]" in result_part.upper()
                            
                            # SKIP SAFE LOGS FOR EVERY AGENT *EXCEPT* USB
                            if is_safe and agent != "usb":
                                continue
                                
                            logs_printed = True
                                
                            pdf.set_font("Arial", 'B', 10)
                            pdf.set_text_color(100, 100, 150) 
                            pdf.cell(0, 6, timestamp, 0, 1)
                            
                            pdf.set_font("Arial", '', 10)
                            pdf.set_text_color(60, 60, 60)
                            pdf.multi_cell(0, 5, f"Data: {data_part}")
                            
                            if result_part:
                                # PHYSICAL DRIVE BYPASS FORMATTING
                                if is_safe and agent == "usb":
                                    pdf.set_text_color(80, 80, 80) # Normal grayish color
                                    pdf.set_font("Arial", '', 10)  # Normal font weight
                                    pdf.multi_cell(0, 5, "Verdict: [SAFE] - Drive scanned and appears clean.")
                                    
                                elif "[ERROR]" in result_part.upper():
                                    pdf.set_text_color(200, 100, 0)
                                    if len(result_part) > 120: result_part = result_part[:117] + "... [TRUNCATED]"
                                    pdf.set_font("Arial", 'B', 10)
                                    pdf.multi_cell(0, 5, f"Verdict: {result_part}")
                                    
                                else:
                                    # SUSPICIOUS / THREAT FORMATTING (Keep Red and Bold)
                                    pdf.set_text_color(200, 0, 0) 
                                    pdf.set_font("Arial", 'B', 10)
                                    pdf.multi_cell(0, 5, f"Verdict: {result_part}")
                            
                            pdf.ln(2)
                            pdf.set_draw_color(230, 230, 230)
                            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                            pdf.ln(2)
            
            if not logs_printed:
                pdf.set_font("Arial", 'I', 10)
                pdf.set_text_color(0, 128, 0)
                pdf.cell(0, 8, "No active threats detected by this agent.", 0, 1)
                
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

        try: self.mascot_img = ImageTk.PhotoImage(Image.open(resource_path("assets/mascot.png")).resize((100, 100)))
        except: self.root.destroy(); return
        try: self.greet_img = ImageTk.PhotoImage(Image.open(resource_path("assets/mascot_greet.png")).resize((100, 100)))
        except: self.greet_img = None 
        try: self.alert_img = ImageTk.PhotoImage(Image.open(resource_path("assets/mascot_alert.png")).resize((100, 100)))
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
        
        self.agent1_on, self.agent2_on, self.agent3_on, self.agent4_on, self.agent5_on, self.agent6_on = True, True, True, True, True, True

        self.running = True
        self.previous_clipboard = ""
        self.is_hotkey_scanning = False
        
        # --- NEW WEB CACHE MEMORY ---
        self.web_cache = {}
        self.current_stable_title = ""
        self.stable_title_timer = 0
        
        try: keyboard.add_hotkey('`', self.trigger_caps_scan, suppress=True)
        except: pass
        
        threading.Thread(target=self.ai_background_loop, daemon=True).start()

    def trigger_alert_emotion(self):
        if self.alert_img:
            self.label.configure(image=self.alert_img)
            self.root.after(4000, lambda: self.label.configure(image=self.mascot_img)) 

    def trigger_caps_scan(self, event=None):
        if not self.agent1_on: return
        if getattr(self, 'is_hotkey_scanning', False): return 
        
        self.is_hotkey_scanning = True 
        
        def execute_hotkey():
            try:
                self.log_to_dashboard("> [Hotkey] Backtick (`) pressed! Grabbing text...")
                time.sleep(0.1) 
                keyboard.send('ctrl+c') 
                time.sleep(0.3)
                text = pyperclip.paste()
                
                if len(text) > 2 and text != self.previous_clipboard:
                    res = analyze_threat("clipboard", text)
                    clean_msg = res.split("] ")[-1] if "] " in res else res
                    write_to_log("clipboard", f"Text: {text[:30]}... | Result: {res}")
                    
                    if "[ERROR]" in res.upper():
                        self.log_to_dashboard(f"⚠️ {clean_msg}")
                    elif "[SAFE]" not in res.upper():
                        self.root.after(0, self.trigger_alert_emotion)
                        send_alert("⚠️ Threat Detected in Text!", clean_msg)
                        self.log_to_dashboard(res)
                    else:
                        send_alert("✅ Clipboard Safe", clean_msg)
                        self.log_to_dashboard(res)
                        
                    self.previous_clipboard = text 
                    
                elif text == self.previous_clipboard:
                    self.log_to_dashboard("> [Hotkey] Text unchanged. Skipping duplicate scan.")
                    
            except Exception as e:
                self.log_to_dashboard(f"> [Error] Hotkey failed: {e}")
            finally:
                time.sleep(1.5)
                self.is_hotkey_scanning = False 
                
        threading.Thread(target=execute_hotkey, daemon=True).start()

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
        if len(self.session_history) > 10: 
            self.session_history.pop(0)
            
        if self.dashboard_open and self.dashboard_ref: 
            self.root.after(0, self.dashboard_ref.add_log_text, message)

    def ai_background_loop(self):
        self.log_to_dashboard("> System Initialized...")
        send_alert("Net Immune Online", "Click the mascot to view the dashboard.")
        
        process_timer = 0
        known_drives = [p.device for p in psutil.disk_partitions() if 'removable' in p.opts.lower() or 'cdrom' not in p.opts.lower()]
        
        try: self.known_downloads = os.listdir(DOWNLOADS_FOLDER)
        except: self.known_downloads = []
        
        last_window_title = ""
        self.previous_clipboard = pyperclip.paste()
        
        while self.running:
            
            if self.agent1_on and not getattr(self, 'is_hotkey_scanning', False): 
                try:
                    curr_clip = pyperclip.paste()
                    
                    if curr_clip != self.previous_clipboard and len(curr_clip) > 5:
                        self.log_to_dashboard("\n[Clipboard] Auto-Scanning...")
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
                            send_alert("✅ Clipboard Safe", clean_msg)
                            self.log_to_dashboard(res)
                            
                        self.previous_clipboard = curr_clip
                except Exception: pass

            if self.agent3_on:
                try:
                    current_downloads = os.listdir(DOWNLOADS_FOLDER)
                    new_files = [f for f in current_downloads if f not in self.known_downloads and not f.endswith(".tmp") and not f.endswith(".crdownload") and not f.endswith(".quarantine")]
                    
                    for new_file in new_files:
                        self.known_downloads.append(new_file) 
                        self.log_to_dashboard(f"\n[Downloads] Scanning new file: {new_file}")
                        
                        full_path = os.path.join(DOWNLOADS_FOLDER, new_file)
                        
                        try:
                            file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                            if file_size_mb > 15.0:
                                content_peek = f"[File too large ({round(file_size_mb, 1)} MB). Analyzed filename only.]"
                            else:
                                with open(full_path, 'rb') as f:
                                    content_peek = f.read(2048).decode('utf-8', errors='ignore')
                        except:
                            content_peek = "[Unreadable Binary]"

                        payload = f"Filename: {new_file}\nInternal File Code/Headers: {content_peek}"
                        res = analyze_threat("file", payload)
                        
                        clean_msg = res.split("] ")[-1] if "] " in res else res
                        write_to_log("folder", f"File: {new_file} | Result: {res}")
                        
                        if "[ERROR]" in res.upper():
                            self.log_to_dashboard(f"⚠️ {clean_msg}")
                        elif "[SAFE]" not in res.upper():
                            self.root.after(0, self.trigger_alert_emotion)
                            send_alert("🚨 Malicious Download Intercepted!", clean_msg)
                            self.log_to_dashboard(res)
                            
                            quarantine_path = full_path + ".quarantine"
                            try:
                                os.rename(full_path, quarantine_path)
                                revoke_1 = tkinter.messagebox.askyesno(
                                    "Net Immune - Threat Intercepted",
                                    f"🚨 MALICIOUS FILE CAUGHT: {new_file}\n\nAI Verdict: {clean_msg}\n\nDo you want to REVOKE and permanently delete this file? (Recommended)\n\nClick YES to Delete.\nClick NO to Run Anyway."
                                )
                                
                                if revoke_1:
                                    os.remove(quarantine_path)
                                    tkinter.messagebox.showinfo("System Secured", f"✅ {new_file} was successfully deleted.\n\nYour PC is safe.")
                                    self.log_to_dashboard(f"> [Deleted] {new_file} destroyed.")
                                else:
                                    run_anyway = tkinter.messagebox.askyesno(
                                        "Net Immune - CRITICAL CAUTION",
                                        f"⚠️ CRITICAL WARNING ⚠️\n\nYou are attempting to bypass security.\nThis file is highly likely to damage your PC, steal data, or install ransomware.\n\nAre you ABSOLUTELY sure you want to restore {new_file}?\n\nClick YES to Run Anyway.\nClick NO to Cancel and Delete."
                                    )
                                    
                                    if run_anyway:
                                        os.rename(quarantine_path, full_path)
                                        self.log_to_dashboard(f"> [Bypassed] User forcefully restored {new_file}.")
                                    else:
                                        os.remove(quarantine_path)
                                        tkinter.messagebox.showinfo("System Secured", f"✅ Smart choice.\n\n{new_file} was successfully deleted.")
                                        self.log_to_dashboard(f"> [Deleted] {new_file} destroyed.")
                                        
                            except Exception as trap_door_err:
                                self.log_to_dashboard(f"> [Trap Door Error] {trap_door_err}")
                        else:
                            send_alert("✅ Download Safe", clean_msg)
                            self.log_to_dashboard(res)
                            
                except Exception: pass

            if self.agent4_on and gw:
                try:
                    raw_title = gw.getActiveWindowTitle()
                    if raw_title:
                        active_title = re.sub(r'^\(\d+\)\s*', '', raw_title)
                        
                        lower_title = active_title.lower()
                        browsers = ["chrome", "brave", "edge", "firefox", "opera"]
                        ignored = ["new tab", "start page", "untitled"]
                        
                        is_browser = any(b in lower_title for b in browsers)
                        is_ignored = any(i in lower_title for i in ignored)

                        if is_browser and not is_ignored:
                            if active_title == self.current_stable_title:
                                self.stable_title_timer += 1
                            else:
                                self.current_stable_title = active_title
                                self.stable_title_timer = 0

                            if self.stable_title_timer == 4 and active_title != last_window_title:
                                
                                if active_title in self.web_cache:
                                    res = self.web_cache[active_title]
                                    if "[ERROR]" not in res.upper() and "[SAFE]" not in res.upper():
                                        keyboard.send('ctrl+w')
                                        self.root.after(0, self.trigger_alert_emotion)
                                        send_alert("🛡️ Threat Tab Terminated!", f"Force-closed a known malicious site:\n{active_title[:40]}")
                                        self.log_to_dashboard(f"> [Web Killer] Terminated re-visit to: {active_title[:30]}...")
                                    else:
                                        self.log_to_dashboard(f"> [Web Cache] Known safe site: {active_title[:30]}...")
                                else:
                                    self.log_to_dashboard(f"\n[Web Monitor] Checking site: {active_title[:30]}...")
                                    res = analyze_threat("web", active_title)
                                    self.web_cache[active_title] = res 
                                    
                                    clean_msg = res.split("] ")[-1] if "] " in res else res
                                    write_to_log("network", f"Web: {active_title[:40]} | Result: {res}")
                                    
                                    if "[ERROR]" in res.upper():
                                        self.log_to_dashboard(f"⚠️ {clean_msg}")
                                    elif "[SAFE]" not in res.upper():
                                        keyboard.send('ctrl+w')
                                        self.root.after(0, self.trigger_alert_emotion)
                                        send_alert("🚨 Malicious Site Terminated!", f"Net Immune force-closed the tab.\nReason: {clean_msg}")
                                        self.log_to_dashboard(f"> [Web Killer] Executed ctrl+w on: {active_title[:30]}...")
                                    else:
                                        send_alert("✅ Web Environment Safe", clean_msg)
                                        self.log_to_dashboard(res)
                                        
                                last_window_title = active_title
                except Exception: pass

            if self.agent5_on:
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
                            
                            # --- NEW ACTIVE USB EJECTOR ---
                            def eject_usb():
                                eject_choice = tkinter.messagebox.askyesno(
                                    "Net Immune - USB Threat",
                                    f"🚨 THREAT DETECTED ON USB: {drive}\n\nAI Verdict: {clean_msg}\n\nDo you want Net Immune to forcefully EJECT this drive to protect your system?\n\nClick YES to Eject.\nClick NO to Ignore."
                                )
                                if eject_choice:
                                    try:
                                        # Uses Windows PowerShell to physically eject the drive safely
                                        drive_letter = drive[:2] # Gets exactly 'E:' or 'F:'
                                        ps_command = f"(New-Object -comObject Shell.Application).Namespace(17).ParseName('{drive_letter}').InvokeVerb('Eject')"
                                        subprocess.run(["powershell", "-Command", ps_command], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                                        
                                        tkinter.messagebox.showinfo("System Secured", f"✅ Drive {drive_letter} has been forcefully ejected.\n\nYou may now remove the physical USB safely.")
                                        self.log_to_dashboard(f"> [Quarantine] USB {drive_letter} forcefully ejected by AI.")
                                    except Exception as eject_err:
                                        self.log_to_dashboard(f"> [Eject Error] {eject_err}")

                            self.root.after(0, eject_usb)
                        else:
                            send_alert("✅ USB Drive Safe", clean_msg)
                            self.log_to_dashboard(res)
                            
                    known_drives = current_drives
                except Exception: pass
                
            if self.agent6_on:
                process_timer += 1
                if process_timer >= 600: 
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
                            proc_str = "\n".join([f"Process: {n} | Usage: {c}%" for n, c in procs])
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
                                send_alert("✅ Processes Safe", "Memory and CPU are secure.")
                                self.log_to_dashboard("✅ PROCESS: Memory secure.")
                    except: pass
                    process_timer = 0
            
            time.sleep(0.5) 

def start_main_app():
    config = load_data(CONFIG_FILE, {"theme": "dark"})
    ctk.set_appearance_mode(config.get("theme", "dark"))
    ctk.set_default_color_theme("green")

    root = tk.Tk()
    try: root.iconbitmap(resource_path("assets/mascot.ico"))
    except: pass
    
    root.geometry(f"100x100+{(root.winfo_screenwidth() // 2) - 50}+20")
    app = FloatingMascot(root)
    root.mainloop()

if __name__ == "__main__":
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Net Immune') 
    except: pass

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
