<div align="center">

# 🛡️ NET IMMUNE
**An Autonomous Multi-Agent AI System for Real-Time Endpoint Threat Neutralization**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Llama-3](https://img.shields.io/badge/Meta_Llama_3-70B-006688?style=for-the-badge&logo=meta&logoColor=white)
![Groq](https://img.shields.io/badge/Powered_by-Groq_API-f37626?style=for-the-badge&logo=lightning&logoColor=white)
![Windows](https://img.shields.io/badge/Platform-Windows_10%2F11-0078d7?style=for-the-badge&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Protection-34C759?style=for-the-badge)

<img src="mascot.png" alt="Net Immune Mascot" width="150"/>

*Shift from static signature-matching to dynamic, AI-driven behavioral analysis.*

</div>

---

## 📖 About The Project

Traditional antivirus software relies on outdated malware signatures, leaving systems vulnerable to zero-day attacks and social engineering. **Net Immune** acts as a localized, AI-powered bodyguard. By integrating the blazing-fast Groq API with Meta's Llama-3 70B model, it continuously monitors system activity, analyzes context, and neutralizes threats in real-time without disrupting the user workflow.

The entire application runs as a lightweight, borderless desktop widget engineered with strict memory management and multi-threaded background processing.

---

## ✨ Core Features & The 5 Agents

Net Immune divides its monitoring capabilities into 5 concurrent, multi-threaded security agents:

* 📋 **Clipboard Watchdog:** Instantly scans copied text, URLs, and scripts to intercept phishing links and extortion scams before they are executed.
* 📁 **Dropzone Scanner:** A dedicated sandbox directory. Any file dropped here is immediately ingested and analyzed for malicious payloads or hacker scripts.
* 🌐 **Network Monitor:** Executes passive background OS scans to identify suspicious outbound connections and rogue listening ports (e.g., unexpected Port 4444 activity).
* 💾 **USB / Drive Scanner:** Monitors the motherboard for newly inserted removable media, intercepting localized hardware threats.
* ⚙️ **Process Watchdog:** Scans active RAM and CPU utilization to detect hidden crypto-miners and unauthorized background tasks.

### 🎨 UI / UX Innovations
* **Floating OS Widget:** A zero-GPU transparent window utilizing mathematical drag-physics for a borderless desktop experience.
* **Fluid Transitions:** Custom canvas-based Water Drop animations for seamless Light/Dark mode toggling.
* **Enterprise Safeguards:** Includes a Kernel-level Mutex lock to prevent duplicate instances, and a localized JSON state-management system with a one-click Factory Reset protocol.

---

## 🏗️ System Architecture

```text
Net Immune App
 ├── Frontend (UI Thread)
 │    ├── CustomTkinter Dashboard
 │    ├── Dynamic Routing (Settings vs. Main)
 │    └── Native Windows Toast Notifications
 │
 └── Backend (Daemon Thread)
      ├── Watchdog Infinite Loop (1s intervals)
      ├── OS-Level Data Extraction (psutil, pyperclip)
      └── HTTPX Async Connection -> Groq API (Llama-3)
```
🚀 Installation & Setup
We have automated the deployment pipeline using Windows Batch scripting to ensure a flawless, isolated environment.

Prerequisites: You must have Python installed and added to your Windows PATH. You will also need a free Groq API Key.
Open cmd in the windows and type this to clone this.

Clone the repository:
```
Bash
git clone https://github.com/Kamalesh-S2k5-RR/Net_Immune.git
cd Net_Immune
```
LOCATION:
C:/user/(your user name)/net_immune

Build the Environment:

Double-click setup.bat. This will automatically create an isolated .venv folder and install all necessary dependencies (CustomTkinter, Psutil, Groq, etc.).

Launch the Engine:

Double-click Start_Net_Immune.bat. This bypasses the terminal entirely, launching the UI natively.

Initialization:

Paste your Groq API key into the sleek setup wizard. The app will verify the connection, reboot, and deploy the desktop mascot.

📊 Analytics & Reporting
Net Immune actively logs its findings.

Real-time metrics are visible in the Settings dashboard, filterable by Today, This Month, and All Time.

Click Export Report to aggregate the /Logs directory into a clean text file for IT review.

👨‍💻 Development Team
This system was engineered and developed by:

*Kamalesh S 
*John Peter V 
*Junaid Ahmed J
*Lingesh M


<div align="center">
<i>Stay Secure. Stay Immune.</i>
</div>
