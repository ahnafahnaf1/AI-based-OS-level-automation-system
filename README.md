# ⚡ JARVIS 2.0 • Windows Desktop Controller

A cyberpunk-themed, mobile-sized AI desktop assistant that controls Windows applications (opening, closing, listing, and PowerShell/CMD commands) using **Groq Tool Calling** with real-time **Text-to-Speech (TTS) voice replies**, authentic **Iron Man J.A.R.V.I.S. & F.R.I.D.A.Y. voices**, expanded **Tamil neural voices**, and an animated **Cyberpunk HUD circular visual voice indicator**.

---

## 🌟 JARVIS 2.0 Features & Capabilities

- **Iron Man Startup Protocol & Voice Welcome:**
  - On launch, the system automatically greets you like Tony Stark:
    - *“Good morning / afternoon / evening, sir. All systems are initialized and ready for work.”* (or *"boss"* for FRIDAY).
  - High-definition neural audio stream with animated HUD ring visualizer.

- **Expanded English Voice Suite (Iron Man Personas):**
  - **J.A.R.V.I.S. (British Male • Iron Man):** Authentic Paul Bettany British tone (`en-GB-RyanNeural`).
  - **F.R.I.D.A.Y. (Irish/British Female • Iron Man):** Kerry Condon style AI assistant (`en-GB-SoniaNeural`).
  - **F.R.I.D.A.Y. (Soft Female AI):** Sleek, soft robotic voice (`en-GB-LibbyNeural`).
  - **J.A.R.V.I.S. Core (Deep British Male):** Authoritative tactical voice (`en-GB-ThomasNeural`).
  - **Guy, Jenny, Aria & Christopher:** Classic American tech AI voices.

- **Expanded 8-Voice Tamil Neural Suite (All Regions):**
  - **India:** `Pallavi (Female • India)`, `Valluvar (Male • India)`.
  - **Sri Lanka:** `Saranya (Female • Sri Lanka)`, `Kumar (Male • Sri Lanka)`.
  - **Malaysia:** `Kani (Female • Malaysia)`, `Surya (Male • Malaysia)`.
  - **Singapore:** `Venba (Female • Singapore)`, `Anbu (Male • Singapore)`.
  - **Automatic Language Detection:** When a response contains Tamil script (தமிழ்) or conversational Tanglish (*"open panniyachu"*, *"close panniten"*, *"vanakkam"*), speech is routed instantaneously to the selected Tamil neural voice!

- **Vision-based Autonomous GUI Agent (Groq Free Tier Shield):**
  - **Autonomous Perception-Action Loop:** Visually inspects the desktop screen and autonomously clicks, types, scrolls, and navigates desktop apps and websites to accomplish high-level objectives (e.g. *"Search Iron Man trailer on YouTube and play it"*).
  - **Groq Free Tier Rate-Limit Shield (429 Handling):**
    - **Exponential Backoff with Jitter:** On HTTP 429, extracts the `retry-after` header or backs off (`min(60, 2**attempt + random.uniform(1, 3))`), retrying up to 4 times with automated model failover.
    - **Step Throttling:** Enforces a mandatory `3.5s` cooldown between successive perception steps to safeguard the Tokens-Per-Minute (TPM/RPM) ceiling.
  - **Aggressive Token Optimization (Image Compression):**
    - Downscales screenshots to a maximum width of `1280px` (LANCZOS).
    - Compresses to `quality=75` JPEG Base64 payload (~5KB per step vs 5MB uncompressed).
    - Automatically calculates 1:1 coordinate scaling factors (`scale_x`, `scale_y`).
  - **Hybrid Fast-Path (Shortcuts First, Vision Second):**
    - Deterministic goals (e.g. *"Open YouTube and search X"*, *"Google X"*, *"Open Notepad"*) execute instantaneous system commands and browser URLs directly, bypassing wasted visual clicking steps.
  - **PyAutoGUI Safety Guardrails:**
    - `FAILSAFE = True` enabled: Moving mouse cursor violently to any corner aborts immediately.
    - `PAUSE = 0.5s` anti-hang guard.
    - Unicode-safe typing via `pyperclip` clipboard paste + `Ctrl+V` (prevents special character drops).
    - Strict `max_steps = 10` timeout limit with final screenshot capture and voice announcement.
  - **Emergency Abort Controls:**
    - Dedicated glowing red **`[🛑 ABORT]`** button appears dynamically in the HUD during autonomous runs.
    - Press **`Escape`** or type `"abort"` in chat to cancel instantly.
    - Send `/abort` from Telegram to cancel remote sessions.
  - **Rich Chat Timeline Logging:**
    - Real-time step cards with AI thought, action target, and visual thumbnail screenshot.

- **Telegram Bot Remote Workstation Control (@SystJarvisBot):**
  - **Full Remote AI Agent Access:** Send instructions directly from Telegram to command your Windows PC from anywhere in the world.
  - **Passcode Security Gatekeeper:** When the bot starts or any user messages the bot, it requires authorization password validation (default: `1234`) before executing any commands or queries.
  - **Remote Screen Capture (`Send screenshot`):** Ask the Telegram bot to *"send screenshot"*, *"take screenshot"*, or *"capture screen"*, and JARVIS captures the Windows desktop in real-time using native Win32 GDI and instantly dispatches the image back to Telegram!
  - **Full Local Tool Execution:** Commands received from authenticated Telegram operators execute Windows apps, PowerShell/CMD tasks, website navigation, and query active processes, broadcasting both in the local desktop HUD and back to Telegram.
  - **Session Lock:** Type `/lock` or `lock` from Telegram to instantly lock the remote session and require passcode entry again.

- **Terminal Command Execution (PowerShell & CMD):**
  - Direct shell tool `execute_command(command: str, shell_type: str)` granting full terminal access.
  - Automatically queries installed apps (via `Get-StartApps` or registry), inspects disks, network configuration (`ipconfig`), running services, or runs any custom script and returns stdout/stderr directly to the AI model.

- **Right-Docked Cyberpunk HUD Form Factor & Glassmorphism:**
  - Automatically launches **docked to the right side of the screen** with the default mobile aspect ratio (**`375 x 665`**).
  - **Stationary Holographic Background:** Background Arc Reactor, HUD reticles, and multi-tier PCB circuits stay permanently fixed in viewport space and never drift or scroll when scrolling through chat messages.
  - **Multi-Layered Cyber Background Effects:** Includes a dynamic concentric Arc Reactor core (crosshairs, tick rings, HUD text), holographic digital dot-matrix grid, multi-stage PCB circuit buses, and wide-screen diagnostic telemetry cards.
  - **Frosted Glassmorphism Message Bubbles:** Semi-translucent frosted glass cards with 3D specular light reflections along the top edge, glowing electric neon borders (`#00f0ff` for AI, `#ff007f` for User), frosted pill badges, ambient dot indicators, and responsive dynamic text wrapping.
  - **Zero Right Scrollbars:** Scrollbars are completely hidden for a clean floating look, while mousewheel scrolling remains fully active.
  - **Full Window Controls Enabled:** Standard Windows Minimize (`_`), Maximize (`□`), and Resizing options remain active with dynamic background circuit auto-scaling!

- **Round Cyberpunk Visual Voice Indicator:**
  - A dynamic, pulsating circular HUD pops up whenever the agent speaks.
  - Highlights `JARVIS // VOICE` or `FRIDAY // VOICE` in cyan, and `TAMIL // VOICE` in hot magenta.

- **Autonomous & Manual Vision Control (Groq Token Saver):**
  - **State Management & HUD Toggle:** Persistent `is_vision_enabled` state (defaults to `OFF` to conserve tokens). A sleek cyber-styled button in the status row allows one-click switching between **`[VISION: OFF]`** (Red/Gray) and **`[VISION: ON]`** (Cyan/Green) with live timeline notices.
  - **Autonomous AI Self-Toggle Tool (`set_vision_state`):** Groq tool calling can autonomously activate vision when visual inspection or UI clicking is strictly required, and turns it back OFF immediately upon task completion to safeguard Free Tier TPM/RPM limits.
  - **Remote Telegram Toggle:** Control vision state from your phone via Telegram (`/vision on`, `/vision off`, or `/vision` status).

- **In-App API Configuration (Settings Screen):**
  - **Groq API Key:** Configure or update your `GROQ_API_KEY` directly inside Settings with Show/Hide toggle and instant `.env` persistence.
  - **Telegram Bot Integration:** Enter or update your `TELEGRAM_BOT_TOKEN` and passcode (`TELEGRAM_BOT_PASSWORD`) from Settings with live gateway status and instant `.env` saving.

- **Dedicated Tabbed Cyber Settings Screen (⚙️ Toggle):**
  - Click the **`⚙`** button in the top bar to access professional 3-tab segmented settings:
    - **`🎙 AUDIO` Tab:**
      - **Default Voice Engine:** Choose whether the default assistant voice is English (Iron Man Suite) or Tamil Neural.
      - **Startup Welcome Greeting:** Choose between English, Tamil, Both, Custom Free Text, or Silent.
      - **Custom Welcome Message (Free Text):** Type any custom greeting (English or Tamil script) with instant test button and persistent saving.
      - **Voice Speech Toggle:** Turn voice feedback `ON` or `OFF`.
      - **Auto Tamil/Tanglish Switch:** Enable or disable automatic language detection for Tamil.
      - **Tamil Voice Persona:** Choose among 8 regional Microsoft Tamil neural voices.
      - **English Voice Persona:** Switch between J.A.R.V.I.S., F.R.I.D.A.Y., and other neural models.
      - **Speech Velocity Slider:** Tune talking speed (130 to 240 WPM).
      - **Audio Diagnostics:** Instant test buttons to sample English, Tamil, and Custom greetings.
    - **`🧠 VISION` Tab:**
      - **Non-Vision First Policy:** Status banner and explanation of token conservation prioritizing direct tools.
      - **Vision Perception Control:** Toggle token-saving vision mode ON/OFF.
      - **Perception Model:** Select Groq vision models (`qwen/qwen3.8-27b`, `llama-3.2-11b-vision-preview`, etc.).
      - **Neural Core Engine:** Switch Groq chat models (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`, etc.).
      - **Guardrails:** Specifications for rate limit shield, image compression, failsafe abort, and step threshold.
    - **`🔑 API LINK` Tab:**
      - **🔑 Groq API Key:** View, edit, hide/show, and save your Groq API key directly to `.env`.
      - **🤖 Telegram Bot Gateway:** Configure bot token and custom passcode with live connection status.
      - **Directives Guide:** Reference cheat sheet for Telegram remote commands.

- **21st.dev Cyber Web Interface (Modern React + Tailwind OS):**
  - Ultra-sleek, modern web user interface inspired by **21st.dev** component design system (`React 18`, `Tailwind CSS`, `Lucide Icons`).
  - **Live Hardware Telemetry Matrix:** Real-time visual gauges for CPU load %, RAM usage, Drive (C:) capacity, Battery/Power status, and Session Uptime.
  - **Dynamic Arc Reactor Voice Visualizer:** Animated cyber core with pulsing frequency equalizer bars during speech broadcasts.
  - **Cyber-Glass Message Feed:** Frosted glassmorphic cards with glowing neon borders, pill badges, collapsible tool cards, and audio replay controls.
  - **Floating Dock Input:** 21st-style floating input bar with quick directive carousel (`System Health`, `Running Apps`, `Chrome`, `Screenshot`, `Vision Toggle`).
  - **Segmented Settings Modal:** Instant dialog for configuring audio personas, velocity, Groq keys, and Telegram credentials.
  - **Native Desktop WebView Window:** Automatically opens inside a dedicated Python native desktop window (via `pywebview` / Edge Chromium WebView2) with zero browser chrome (no address bar, no browser tabs, docked cleanly to the right side of the screen).
  - **Launch with One Click:** Run `python server.py` or double-click `run_web.bat` to launch the native desktop application immediately. Pass `--browser` if you ever want to open in a standard browser tab instead.

- **Mobile Form Factor:**
  - Locked `420 x 720` mobile smartphone aspect ratio.
  - Window resizing, minimize, and maximize buttons disabled for an uncluttered tool window experience.

---

## 📋 Requirements & Installation

1. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   *(Installs `groq`, `customtkinter`, `python-dotenv`, and `pyttsx3`)*

2. **Configure your Environment (.env):**
   Ensure your `.env` contains your Groq API key and Telegram Bot configuration:
   ```env
   GROQ_API_KEY='gsk_your_groq_api_key_here'
   TELEGRAM_BOT_TOKEN='9049041950:AAGCD0KcHkByT_-F34UniaiHII-vEsSekN4'
   TELEGRAM_BOT_PASSWORD='1234'
   ```

---

## 🚀 Running the App

```powershell
python app.py
```

---

## 📦 Building Standalone Single-File Executable (.exe)

The application supports bundling the `.env` file directly inside a standalone single-file `.exe` via PyInstaller.

### Build with one click:
Run `build_exe.bat` or run the following command:
```powershell
pyinstaller jarvis.spec
```

### Alternatively via CLI:
```powershell
pyinstaller --clean --onefile --windowed --add-data ".env;." --collect-all customtkinter --name "JARVIS-2.0" app.py
```

### How .env is Resolved:
1. **Bundled Exe (`sys._MEIPASS`):** First checks if `.env` is packed inside the temporary PyInstaller runtime archive (`sys._MEIPASS/.env`).
2. **Adjacent to `.exe`:** If not bundled, checks for an external `.env` located beside the `.exe` file.
3. **Local Dev Directory:** Falls back to the development source folder.
The resulting single file `dist\JARVIS-2.0.exe` runs independently without needing Python or external `.env` files installed on target machines!

---

### 🤖 Remote Telegram Commands (@SystJarvisBot):
1. Start a chat with `@SystJarvisBot` on Telegram.
2. Send any message or `/start`. JARVIS will challenge you for the security passcode (`1234`).
3. Enter `1234` to authorize your session.
4. Try sending:
   - *"Send screenshot"* ➔ Instantly captures the Windows desktop and sends the photo to Telegram!
   - *"Open Chrome"* / *"Close Notepad"*
   - *"List all apps installed on my PC"*
   - *"What apps are running right now?"*
   - *"Run powershell: Get-Process | select -first 5"*
   - *"/vision on"* / *"/vision off"* ➔ Remotely toggles autonomous vision perception to conserve tokens.
   - *"/vision"* ➔ Checks current vision perception mode.
   - *"/lock"* ➔ Locks the session.

### 👁️ Autonomous Vision GUI Commands:
- *"auto: Search Iron Man theme song on YouTube and play it"*
- *"auto: Open Google and look up latest AI news"*
- *"Search for funny cat videos on YouTube and click the first video"*
- *"auto: Open Notepad and write 'JARVIS 2.0 Vision Online'"*
- Press **`Escape`** or click **`[🛑 ABORT]`** at any point to cancel instantly.

### 💻 Local Desktop Cyber Commands:
- *"Calculator open pannu nanba"* (Tanglish)
- *"என் கணினியில் நிறுவப்பட்ட அனைத்து பயன்பாடுகளையும் பட்டியலிடுங்கள்"* (Tamil)
- *"Chrome close pannitten, ippo notepad open pannu"* (Tanglish)
- *"List all apps installed in my PC"* (English)
- *"Show my IP address and network config"*
- *"What applications are running right now?"*
- *"Take a screenshot"*
- *"Check available disk space"*
- *"Open github.com"*
