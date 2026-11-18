"""
==============================================================================
Groq Windows Desktop Agent - JARVIS 2.0 Edition
==============================================================================
A cutting-edge, mobile-sized Cyberpunk HUD desktop chat application that controls
Windows applications (opening, closing, inspecting apps) using the Groq API and
Tool Calling (Function Calling).

Features:
- Neon Cyberpunk Aesthetics (OLED Void, Neon Cyan, Hot Magenta, Electric Yellow)
- Text-to-Speech (TTS) Voice Feedback with every AI response
- Settings Screen with Voice Toggle, Voice Character, Speed, and Model Config
- Dynamic Pulsing Round Cyberpunk HUD Visual Voice Indicator during speech
- Mobile aspect ratio (420x720) with non-resizable toolwindow bounds
- Background non-blocking execution for both Groq API and TTS speech

Author: AI Pair Programming Assistant
==============================================================================
"""

import os
import sys
import re
import csv
import io
import json
import math
import time
import shutil
import logging
import datetime
import subprocess
import threading
import webbrowser
import asyncio
import tempfile
import ctypes
import random
import base64
from ctypes import wintypes
from typing import Dict, Any, List, Optional, Tuple, Callable

import requests
from PIL import Image
import tkinter as tk
import customtkinter as ctk
from dotenv import load_dotenv

# PyAutoGUI & PyPerclip for Vision Autonomous GUI Automation
try:
    import pyautogui
    import pyperclip
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
except ImportError:
    pyautogui = None
    pyperclip = None

# Groq API import
try:
    from groq import (
        Groq,
        APIError,
        AuthenticationError,
        RateLimitError,
        APIConnectionError,
        NotFoundError,
    )
except ImportError:
    Groq = None
    APIError = AuthenticationError = RateLimitError = APIConnectionError = NotFoundError = Exception

# Text-to-Speech imports
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import edge_tts
    import pygame
except ImportError:
    edge_tts = None
    pygame = None

# System telemetry imports
import platform
try:
    import psutil
except ImportError:
    psutil = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS-2.0")

# ==============================================================================
# ENVIRONMENT RESOLUTION & LOADING (PyInstaller _MEIPASS + Fallbacks)
# ==============================================================================

def resolve_and_load_env():
    """
    Robust Environment Path Resolution:
    1. Checks PyInstaller's temporary bundled directory (sys._MEIPASS) first.
    2. Falls back to adjacent executable directory (next to .exe).
    3. Falls back to local development script directory.
    """
    # 1. Check if running inside a PyInstaller bundled onefile exe (_MEIPASS)
    if getattr(sys, 'frozen', False):
        bundled_env = os.path.join(getattr(sys, '_MEIPASS', ''), '.env')
        if os.path.exists(bundled_env):
            load_dotenv(dotenv_path=bundled_env, override=True)
            logger.info(f"Loaded bundled environment from PyInstaller _MEIPASS: {bundled_env}")
            return

        # Fallback: check adjacent to the .exe file
        exe_dir_env = os.path.join(os.path.dirname(sys.executable), '.env')
        if os.path.exists(exe_dir_env):
            load_dotenv(dotenv_path=exe_dir_env, override=True)
            logger.info(f"Loaded adjacent environment from executable directory: {exe_dir_env}")
            return

    # 2. Local development fallback
    local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path=local_env)
    logger.info(f"Loaded local development environment: {local_env}")

resolve_and_load_env()

def save_env_variable(key: str, value: str) -> bool:
    """Updates or persists an environment variable into the writable .env file."""
    try:
        if getattr(sys, 'frozen', False):
            env_path = os.path.join(os.path.dirname(sys.executable), '.env')
        else:
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

        lines = []
        key_found = False
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                        lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        lines.append(line)
        if not key_found:
            lines.append(f"{key}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        os.environ[key] = value
        logger.info(f"Persisted {key} to {env_path}")
        return True
    except Exception as ex:
        logger.error(f"Failed writing {key} to .env: {ex}")
        return False

# Default models
DEFAULT_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
]
EXCLUDED_MODEL_KEYWORDS = ["guard", "whisper", "embedding", "safeguard", "orpheus", "allam"]

# Vision Autonomous GUI Agent Constants & Rate-Limit Shield
DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
VISION_MODELS = [
    "qwen/qwen3.8-27b",
    "llama-3.2-11b-vision-preview",
    "llama-3.2-90b-vision-preview",
]
MAX_AUTONOMOUS_STEPS = 10
STEP_THROTTLE_SECONDS = 3.5  # Protects TPM/RPM ceiling on Groq Free Tier
VISION_COMPRESSION_WIDTH = 1280
VISION_COMPRESSION_QUALITY = 75

# Voice Persona Catalogs (Microsoft Neural High-Definition Audio)
ENGLISH_VOICES = {
    "J.A.R.V.I.S. (British Male • Iron Man)": "en-GB-RyanNeural",
    "F.R.I.D.A.Y. (Irish/British Female • Iron Man)": "en-GB-SoniaNeural",
    "F.R.I.D.A.Y. (Soft Female AI)": "en-GB-LibbyNeural",
    "J.A.R.V.I.S. Core (Deep British Male)": "en-GB-ThomasNeural",
    "Guy (American Male AI)": "en-US-GuyNeural",
    "Jenny (American Female AI)": "en-US-JennyNeural",
    "Aria (Neural Female AI)": "en-US-AriaNeural",
    "Christopher (Deep Tech Male)": "en-US-ChristopherNeural",
}

TAMIL_VOICES = {
    "Pallavi (Female • India)": "ta-IN-PallaviNeural",
    "Valluvar (Male • India)": "ta-IN-ValluvarNeural",
    "Saranya (Female • Sri Lanka)": "ta-LK-SaranyaNeural",
    "Kumar (Male • Sri Lanka)": "ta-LK-KumarNeural",
    "Kani (Female • Malaysia)": "ta-MY-KaniNeural",
    "Surya (Male • Malaysia)": "ta-MY-SuryaNeural",
    "Venba (Female • Singapore)": "ta-SG-VenbaNeural",
    "Anbu (Male • Singapore)": "ta-SG-AnbuNeural",
}


# ==============================================================================
# WINDOWS APPLICATION CATALOG & CONTROLLER
# ==============================================================================

APP_CATALOG = {
    "notepad": {
        "display_name": "Notepad",
        "aliases": ["notepad", "note", "notes", "text editor", "texteditor"],
        "commands": ["notepad.exe"],
        "processes": ["notepad.exe"],
    },
    "calculator": {
        "display_name": "Calculator",
        "aliases": ["calculator", "calc", "calculation"],
        "commands": ["calc.exe"],
        "processes": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
    },
    "chrome": {
        "display_name": "Google Chrome",
        "aliases": ["chrome", "google chrome", "google-chrome", "browser"],
        "commands": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "chrome.exe",
            "start chrome"
        ],
        "processes": ["chrome.exe"],
    },
    "edge": {
        "display_name": "Microsoft Edge",
        "aliases": ["edge", "microsoft edge", "ms edge", "msedge"],
        "commands": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "msedge.exe",
            "start msedge"
        ],
        "processes": ["msedge.exe"],
    },
    "vscode": {
        "display_name": "Visual Studio Code",
        "aliases": ["vscode", "vs code", "code", "visual studio code"],
        "commands": ["code.cmd", "code", "code.exe"],
        "processes": ["Code.exe"],
    },
    "paint": {
        "display_name": "Paint",
        "aliases": ["paint", "mspaint", "ms paint"],
        "commands": ["mspaint.exe"],
        "processes": ["mspaint.exe", "Paint.exe"],
    },
    "terminal": {
        "display_name": "Terminal / Command Prompt",
        "aliases": ["cmd", "command prompt", "terminal", "windows terminal", "wt", "console"],
        "commands": ["wt.exe", "cmd.exe"],
        "processes": ["WindowsTerminal.exe", "cmd.exe"],
    },
    "powershell": {
        "display_name": "PowerShell",
        "aliases": ["powershell", "pwsh", "posh"],
        "commands": ["powershell.exe"],
        "processes": ["powershell.exe"],
    },
    "explorer": {
        "display_name": "File Explorer",
        "aliases": ["explorer", "file explorer", "files", "my computer", "windows explorer"],
        "commands": ["explorer.exe"],
        "processes": ["explorer.exe"],
    },
    "taskmanager": {
        "display_name": "Task Manager",
        "aliases": ["task manager", "taskmgr", "task-manager", "tasks"],
        "commands": ["taskmgr.exe"],
        "processes": ["Taskmgr.exe"],
    },
    "settings": {
        "display_name": "Windows Settings",
        "aliases": ["settings", "windows settings", "ms settings"],
        "commands": ["start ms-settings:"],
        "processes": ["SystemSettings.exe"],
    },
    "spotify": {
        "display_name": "Spotify",
        "aliases": ["spotify", "music player"],
        "commands": ["spotify.exe", "start spotify:"],
        "processes": ["Spotify.exe"],
    },
    "snippingtool": {
        "display_name": "Snipping Tool",
        "aliases": ["snipping tool", "snip", "snippingtool", "screen snip"],
        "commands": ["snippingtool.exe"],
        "processes": ["SnippingTool.exe", "ScreenClippingHost.exe"],
    },
    "wordpad": {
        "display_name": "WordPad",
        "aliases": ["wordpad", "write"],
        "commands": ["wordpad.exe"],
        "processes": ["wordpad.exe"],
    },
    "controlpanel": {
        "display_name": "Control Panel",
        "aliases": ["control panel", "control"],
        "commands": ["control.exe"],
        "processes": ["control.exe"],
    },
}

ALIAS_MAP: Dict[str, str] = {}
for key, data in APP_CATALOG.items():
    ALIAS_MAP[key] = key
    for alias in data.get("aliases", []):
        ALIAS_MAP[alias.lower().strip()] = key


def resolve_app_key(app_name: str) -> Optional[str]:
    cleaned = app_name.lower().strip()
    if cleaned in ALIAS_MAP:
        return ALIAS_MAP[cleaned]
    for alias, key in ALIAS_MAP.items():
        if alias in cleaned or cleaned in alias:
            return key
    return None


def open_application(app_name: str) -> Dict[str, Any]:
    logger.info(f"Executing open_application for: '{app_name}'")
    key = resolve_app_key(app_name)

    if key and key in APP_CATALOG:
        entry = APP_CATALOG[key]
        display_name = entry["display_name"]
        commands = entry["commands"]

        for cmd in commands:
            try:
                if cmd.startswith("start "):
                    subprocess.Popen(cmd, shell=True)
                    return {
                        "status": "success",
                        "app_name": display_name,
                        "message": f"Successfully launched {display_name}."
                    }
                else:
                    if os.path.isabs(cmd) and not os.path.exists(cmd):
                        continue
                    subprocess.Popen(f'start "" "{cmd}"' if " " in cmd else cmd, shell=True)
                    return {
                        "status": "success",
                        "app_name": display_name,
                        "message": f"Successfully launched {display_name}."
                    }
            except Exception:
                continue

    # Fallback to system PATH or Shell
    raw_name = app_name.strip()
    try:
        resolved_bin = shutil.which(raw_name) or shutil.which(f"{raw_name}.exe")
        if resolved_bin:
            subprocess.Popen([resolved_bin])
            return {
                "status": "success",
                "app_name": raw_name,
                "message": f"Successfully launched {raw_name} from system PATH."
            }
        subprocess.Popen(f'start "" "{raw_name}"', shell=True)
        return {
            "status": "success",
            "app_name": raw_name,
            "message": f"Sent launch command for '{raw_name}' via Windows Shell."
        }
    except Exception as ex:
        logger.error(f"Error opening '{raw_name}': {ex}")
        return {
            "status": "error",
            "app_name": raw_name,
            "message": f"Failed to open '{raw_name}': {str(ex)}"
        }


def close_application(app_name: str) -> Dict[str, Any]:
    logger.info(f"Executing close_application for: '{app_name}'")
    key = resolve_app_key(app_name)

    targets: List[str] = []
    display_name = app_name.strip()

    if key and key in APP_CATALOG:
        entry = APP_CATALOG[key]
        display_name = entry["display_name"]
        targets = list(entry["processes"])
    else:
        clean_name = app_name.strip()
        if clean_name.lower().endswith(".exe"):
            targets = [clean_name]
        else:
            targets = [f"{clean_name}.exe", clean_name]

    killed_any = False
    killed_processes = []
    errors = []

    for proc in targets:
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                killed_any = True
                killed_processes.append(proc)
            elif res.returncode == 128:
                pass
            else:
                if res.stderr and "not found" not in res.stderr.lower():
                    errors.append(res.stderr.strip())
        except Exception as ex:
            errors.append(str(ex))

    if killed_any:
        return {
            "status": "success",
            "app_name": display_name,
            "message": f"Successfully closed {display_name} ({', '.join(killed_processes)})."
        }
    elif errors:
        return {
            "status": "error",
            "app_name": display_name,
            "message": f"Error terminating {display_name}: {'; '.join(errors)}"
        }
    else:
        return {
            "status": "not_running",
            "app_name": display_name,
            "message": f"{display_name} is not currently running."
        }


def list_running_applications() -> Dict[str, Any]:
    logger.info("Executing list_running_applications query...")
    try:
        res = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False
        )
        reader = csv.reader(io.StringIO(res.stdout))
        running_set = set(row[0].lower() for row in reader if row)

        found = []
        for key, data in APP_CATALOG.items():
            for p in data["processes"]:
                if p.lower() in running_set:
                    found.append(data["display_name"])
                    break

        return {
            "status": "success",
            "running_applications": found,
            "count": len(found),
            "message": f"Found {len(found)} active application(s): {', '.join(found) if found else 'None'}."
        }
    except Exception as ex:
        logger.error(f"Failed to query running applications: {ex}")
        return {
            "status": "error",
            "message": f"Could not list running applications: {str(ex)}"
        }


def open_website(url: str) -> Dict[str, Any]:
    logger.info(f"Executing open_website for: '{url}'")
    try:
        cleaned_url = url.strip()
        if not cleaned_url.startswith("http://") and not cleaned_url.startswith("https://"):
            cleaned_url = f"https://{cleaned_url}"
        webbrowser.open(cleaned_url)
        return {
            "status": "success",
            "url": cleaned_url,
            "message": f"Opened {cleaned_url} in your browser."
        }
    except Exception as ex:
        logger.error(f"Error opening URL '{url}': {ex}")
        return {
            "status": "error",
            "url": url,
            "message": f"Failed to open website: {str(ex)}"
        }


def get_system_health() -> Dict[str, Any]:
    """
    Collects comprehensive hardware, memory, disk, CPU, power, and process telemetry
    for AI diagnostic evaluation and analysis.
    """
    logger.info("Executing get_system_health telemetry probe...")
    if psutil is None:
        return {
            "status": "error",
            "message": "psutil library is not available. Please install psutil (pip install psutil).",
            "diagnostics": {}
        }

    try:
        # 1. CPU Telemetry
        cpu_usage = psutil.cpu_percent(interval=0.08)
        logical_cores = psutil.cpu_count(logical=True) or 1
        physical_cores = psutil.cpu_count(logical=False) or 1
        freq = psutil.cpu_freq()
        cpu_freq_ghz = round(freq.current / 1000.0, 2) if freq and freq.current else None

        # 2. RAM / Memory Telemetry
        vm = psutil.virtual_memory()
        total_ram_gb = round(vm.total / (1024**3), 2)
        used_ram_gb = round(vm.used / (1024**3), 2)
        free_ram_gb = round(vm.available / (1024**3), 2)
        ram_percent = vm.percent

        # 3. Disk Storage Telemetry (Primary Fixed Drives)
        drives = []
        for part in psutil.disk_partitions(all=False):
            if not part.fstype or "cdrom" in part.opts:
                continue
            try:
                du = psutil.disk_usage(part.mountpoint)
                drives.append({
                    "drive": part.mountpoint,
                    "total_gb": round(du.total / (1024**3), 1),
                    "used_gb": round(du.used / (1024**3), 1),
                    "free_gb": round(du.free / (1024**3), 1),
                    "usage_percent": du.percent
                })
            except (PermissionError, OSError):
                continue

        # 4. Battery & Power Telemetry
        battery_data = {"present": False, "percent": 100, "plugged_in": True, "status": "AC Power (Desktop/Docked)"}
        if hasattr(psutil, "sensors_battery"):
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    battery_data = {
                        "present": True,
                        "percent": bat.percent,
                        "plugged_in": bat.power_plugged,
                        "status": "Charging / AC Power" if bat.power_plugged else "Running on Battery"
                    }
            except Exception:
                pass

        # 5. Top Resource Consuming Processes (Top 5 by aggregated memory)
        top_procs = []
        for p in psutil.process_iter(['name', 'memory_info']):
            try:
                mem_rss = (p.info.get('memory_info').rss or 0) / (1024**2)
                top_procs.append({
                    "name": p.info.get('name') or "Unknown",
                    "memory_mb": round(mem_rss, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                continue

        proc_mem_map = {}
        for p in top_procs:
            pname = p["name"]
            proc_mem_map[pname] = proc_mem_map.get(pname, 0.0) + p["memory_mb"]

        sorted_procs = sorted(proc_mem_map.items(), key=lambda x: x[1], reverse=True)[:5]
        top_consumers = [{"process": name, "total_memory_mb": round(mb, 1)} for name, mb in sorted_procs]

        # 6. Uptime & OS
        boot_ts = psutil.boot_time()
        uptime_sec = int(time.time() - boot_ts)
        days = uptime_sec // 86400
        hours = (uptime_sec % 86400) // 3600
        mins = (uptime_sec % 3600) // 60
        uptime_formatted = f"{days}d {hours}h {mins}m" if days > 0 else f"{hours}h {mins}m"

        os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"

        # 7. Overall Health Classification
        if cpu_usage < 75 and ram_percent < 80:
            health_condition = "Optimal / Healthy"
        elif cpu_usage >= 90 or ram_percent >= 92:
            health_condition = "Critical Load / Memory Pressure"
        else:
            health_condition = "Moderate Workload"

        return {
            "status": "success",
            "condition": health_condition,
            "message": f"Hardware telemetry: CPU {cpu_usage}%, RAM {ram_percent}%, {len(drives)} drive(s) online.",
            "metrics": {
                "cpu": {
                    "usage_percent": cpu_usage,
                    "logical_cores": logical_cores,
                    "physical_cores": physical_cores,
                    "clock_speed_ghz": cpu_freq_ghz
                },
                "memory": {
                    "total_gb": total_ram_gb,
                    "used_gb": used_ram_gb,
                    "free_gb": free_ram_gb,
                    "usage_percent": ram_percent
                },
                "storage_drives": drives,
                "power_battery": battery_data,
                "uptime": uptime_formatted,
                "os": os_info,
                "top_active_consumers": top_consumers
            }
        }
    except Exception as ex:
        logger.error(f"Error gathering system health telemetry: {ex}")
        return {
            "status": "error",
            "message": f"Failed to retrieve system health telemetry: {str(ex)}"
        }


def execute_command(command: str, shell_type: str = "powershell") -> Dict[str, Any]:
    """
    Executes a PowerShell or CMD command in Windows and captures its output.
    Provides full terminal access to query system info, installed applications,
    network configuration, disks, services, files, and more.
    """
    logger.info(f"Executing terminal command [{shell_type}]: '{command}'")
    shell_lower = shell_type.lower().strip()

    try:
        if "cmd" in shell_lower:
            process_args = ["cmd.exe", "/c", command]
        else:
            process_args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command]

        result = subprocess.run(
            process_args,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Limit output length to prevent context explosion if huge
        max_chars = 4000
        truncated = False
        if len(stdout) > max_chars:
            stdout = stdout[:max_chars] + f"\n... [Output truncated: {len(stdout) - max_chars} characters remaining]"
            truncated = True

        status = "success" if result.returncode == 0 else "error"
        output_text = stdout.strip() if stdout.strip() else (stderr.strip() if stderr.strip() else "Command completed with no output.")

        return {
            "status": status,
            "shell": "cmd" if "cmd" in shell_lower else "powershell",
            "command": command,
            "returncode": result.returncode,
            "output": output_text,
            "truncated": truncated,
            "message": f"Command finished with return code {result.returncode}."
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {
            "status": "error",
            "shell": shell_type,
            "command": command,
            "message": "Command execution timed out after 30 seconds."
        }
    except Exception as ex:
        logger.error(f"Error executing command '{command}': {ex}")
        return {
            "status": "error",
            "shell": shell_type,
            "command": command,
            "message": f"Execution failed: {str(ex)}"
        }


def capture_screenshot(output_path: Optional[str] = None) -> str:
    """Captures the full Windows desktop screen using high-speed native Win32 GDI APIs."""
    if not output_path:
        ts = int(datetime.datetime.now().timestamp())
        output_path = os.path.join(tempfile.gettempdir(), f"jarvis_screen_{ts}.png")

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

    w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
    h = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    # SRCCOPY = 0x00CC0020
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD),
        ]

    bih = BITMAPINFOHEADER()
    bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bih.biWidth = w
    bih.biHeight = -h  # top-down DIB
    bih.biPlanes = 1
    bih.biBitCount = 32
    bih.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bih), 0)

    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    img = img.convert('RGB')
    img.save(output_path, 'PNG')

    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    gdi32.DeleteObject(hbmp)
    logger.info(f"Desktop screenshot saved to {output_path} ({w}x{h})")
    return output_path


def take_screenshot(filename: Optional[str] = None) -> Dict[str, Any]:
    """Tool wrapper: Captures a screenshot of the user's desktop."""
    try:
        path = capture_screenshot(filename)
        return {
            "status": "success",
            "file_path": path,
            "message": f"Desktop screenshot successfully captured and stored at {path}."
        }
    except Exception as ex:
        logger.error(f"Error taking screenshot: {ex}")
        return {
            "status": "error",
            "message": f"Failed to capture screenshot: {str(ex)}"
        }


# ==============================================================================
# VISION-BASED AUTONOMOUS GUI AGENT HELPERS & DEFENSIVE ENGINE
# ==============================================================================

VISION_AGENT_SYSTEM_PROMPT = """You are an expert Vision-based Autonomous GUI Agent operating a Windows desktop.
You are given a high-level user GOAL, previous step history, and a current SCREENSHOT of the desktop.
Your task is to visually inspect the screen and determine the exact single next action to take.

IMAGE SPECIFICATIONS:
- The image has resolution {width} x {height} pixels (x in [0, {width}], y in [0, {height}]).
- Coordinate (0, 0) is the TOP-LEFT corner.
- Coordinate ({width}, {height}) is the BOTTOM-RIGHT corner.

AVAILABLE ACTIONS:
- "click": Left-click on an interactive UI element at coordinates (x, y). Target the visual center of buttons, thumbnails, links, or search results.
- "type": Click at coordinates (x, y), type "text", and optionally press "key" (e.g. "enter").
- "press": Press a keyboard key (e.g. "enter", "tab", "escape", "space", "backspace", "up", "down").
- "scroll": Scroll the page. Set "direction": "down" or "up".
- "wait": Pause 1.5s for page/content to render.
- "finish": The user's goal has been completely achieved. Set "is_completed": true.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with ONLY a single, strictly valid JSON object matching this exact schema:
{{
  "thought": "Clear visual observation of the screen elements and rationale for this step",
  "action": "click" | "type" | "press" | "scroll" | "wait" | "finish",
  "x": 640,
  "y": 360,
  "text": null,
  "key": null,
  "is_completed": false
}}

CRITICAL RULES:
1. Coordinates MUST be integers within [0, {width}] and [0, {height}].
2. When clicking buttons, links, search bars, or video thumbnails, provide the exact center coordinates.
3. If the objective is accomplished, set "action": "finish" and "is_completed": true.
4. Output raw JSON only. Do not wrap in markdown quotes or extra text."""


def prepare_vision_screenshot(max_width: int = VISION_COMPRESSION_WIDTH, quality: int = VISION_COMPRESSION_QUALITY) -> Dict[str, Any]:
    """
    Captures native desktop screen, aggressively downscales to max 1280px maintaining aspect ratio,
    and compresses to quality=75 JPEG Base64 payload, computing exact coordinate scaling factors.
    """
    raw_path = capture_screenshot()
    with Image.open(raw_path) as img:
        orig_w, orig_h = img.size
        if orig_w > max_width:
            down_w = max_width
            down_h = int(orig_h * (float(max_width) / float(orig_w)))
            resized = img.resize((down_w, down_h), Image.Resampling.LANCZOS)
        else:
            down_w, down_h = orig_w, orig_h
            resized = img.copy()

        # Compress to JPEG with quality=75
        buffer = io.BytesIO()
        resized.convert("RGB").save(buffer, format="JPEG", quality=quality, optimize=True)
        jpeg_bytes = buffer.getvalue()
        b64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
        b64_data_url = f"data:image/jpeg;base64,{b64_str}"

        # Coordinate scaling factors
        scale_x = float(orig_w) / float(down_w)
        scale_y = float(orig_h) / float(down_h)

        # Save compressed thumbnail to temp file for GUI rendering
        thumb_path = os.path.join(tempfile.gettempdir(), f"vision_step_{int(time.time() * 1000)}.jpg")
        with open(thumb_path, "wb") as f:
            f.write(jpeg_bytes)

        return {
            "data_url": b64_data_url,
            "raw_path": raw_path,
            "thumb_path": thumb_path,
            "down_w": down_w,
            "down_h": down_h,
            "orig_w": orig_w,
            "orig_h": orig_h,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "payload_kb": len(jpeg_bytes) / 1024.0,
        }


def execute_hybrid_fast_path(goal: str) -> Dict[str, Any]:
    """
    Executes deterministic system shortcuts (opening URLs, apps, or search queries)
    before invoking the Vision perception loop, saving tokens and round-trips.
    Prioritizes non-vision direct execution to conserve Groq Free Tier tokens.
    """
    goal_lower = goal.lower().strip()

    # Check if the user specified subsequent visual interaction (e.g. clicking, typing, selecting a specific video)
    has_visual_actions = any(w in goal_lower for w in [
        "click", "press", "type", "select", "choose", "first video", "second video", "submit", "fill", "pause", "resume"
    ])

    # 1. YouTube specific query: e.g. "play X on youtube", "search X on youtube", "open youtube"
    if "youtube" in goal_lower:
        yt_search_match = re.search(r"(?:search|play|find|look up|open youtube and (?:search|play))\s+(?:for\s+)?(.+?)(?:\s+on\s+youtube|\s+in\s+youtube|$)", goal_lower)
        query = ""
        if yt_search_match:
            query = yt_search_match.group(1).replace("youtube", "").strip(" -:")

        if query and query not in ["video", "website", "page", ""]:
            url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
            logger.info(f"Fast-path triggered: Opening YouTube search URL: {url}")
            webbrowser.open(url)
            return {
                "fast_path_used": True,
                "completed": not has_visual_actions,
                "action": "open_url",
                "target": url,
                "message": f"Directly opened YouTube search for '{query}'."
            }
        else:
            url = "https://www.youtube.com"
            webbrowser.open(url)
            return {
                "fast_path_used": True,
                "completed": not has_visual_actions,
                "action": "open_url",
                "target": url,
                "message": "Directly launched YouTube in web browser."
            }

    # 2. Google Search query: e.g. "search X on google", "google X"
    g_match = re.search(r"(?:search|google|look up)\s+(?:for\s+)?(.+?)(?:\s+on\s+google|$)", goal_lower)
    if ("google" in goal_lower or goal_lower.startswith("search ")) and g_match:
        query = g_match.group(1).replace("google", "").strip(" -:")
        if query and not any(k in query for k in ["youtube", "app", "file"]):
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            logger.info(f"Fast-path triggered: Opening Google search URL: {url}")
            webbrowser.open(url)
            return {
                "fast_path_used": True,
                "completed": not has_visual_actions,
                "action": "open_url",
                "target": url,
                "message": f"Directly opened Google search for '{query}'."
            }

    # 3. Direct website URL / domain (e.g. "open github.com", "open reddit", "go to wikipedia.org")
    domain_match = re.search(r"(?:open|go to|browse|visit)\s+([a-zA-Z0-9.-]+\.(?:com|org|net|io|edu|gov|dev|ai|app))", goal_lower)
    if domain_match:
        domain = domain_match.group(1)
        url = f"https://{domain}" if not domain.startswith("http") else domain
        webbrowser.open(url)
        return {
            "fast_path_used": True,
            "completed": not has_visual_actions,
            "action": "open_url",
            "target": url,
            "message": f"Directly opened website '{url}'."
        }

    # 4. Known desktop application: e.g. "open notepad", "open calculator", "open spotify", "open chrome"
    open_app_match = re.search(r"^open\s+([a-zA-Z0-9\s]+)$", goal_lower)
    if open_app_match:
        app_name = open_app_match.group(1).strip()
        app_key = resolve_app_key(app_name)
        if app_key:
            res = open_application(app_name)
            return {
                "fast_path_used": True,
                "completed": True,
                "action": "open_app",
                "target": app_name,
                "message": res.get("message", f"Opened {app_name}")
            }

    return {"fast_path_used": False, "completed": False, "message": "No shortcut matched. Proceeding with Vision perception."}


def call_groq_vision_with_rate_shield(
    client: Groq,
    model: str,
    messages: List[Dict[str, Any]],
    max_retries: int = 4,
    abort_event: Optional[threading.Event] = None,
    on_retry_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Executes a Groq Vision API call wrapped in an industrial-grade Rate-Limit Shield.
    Handles HTTP 429 RateLimitErrors using retry-after header extraction,
    exponential backoff with random jitter, model fallback, and atomic abort event checks.
    """
    current_model = model
    candidate_vision_models = [
        current_model,
        "qwen/qwen3.8-27b",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview"
    ]
    seen = set()
    models_to_try = [m for m in candidate_vision_models if not (m in seen or seen.add(m))]

    model_idx = 0
    attempt = 0

    while attempt <= max_retries:
        if abort_event and abort_event.is_set():
            return {"status": "aborted", "message": "Vision call cancelled by abort event."}

        current_model = models_to_try[model_idx % len(models_to_try)]
        try:
            logger.info(f"Invoking Groq Vision model '{current_model}' (Attempt {attempt + 1}/{max_retries + 1})...")
            response = client.chat.completions.create(
                model=current_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1024
            )
            raw_text = response.choices[0].message.content or "{}"
            return {"status": "success", "content": raw_text, "model": current_model}

        except RateLimitError as rle:
            attempt += 1
            logger.warning(f"Groq 429 RateLimitError on {current_model} (Attempt {attempt}/{max_retries}): {rle}")

            if attempt > max_retries:
                return {
                    "status": "error",
                    "error_type": "rate_limit",
                    "message": f"Groq Rate Limit ceiling reached after {max_retries} retry attempts: {str(rle)}"
                }

            # 1. Check for retry-after in response headers
            wait_seconds = None
            if hasattr(rle, "response") and rle.response is not None:
                header_val = getattr(rle.response, "headers", {}).get("retry-after")
                if header_val:
                    try:
                        wait_seconds = float(header_val) + random.uniform(0.5, 1.5)
                    except ValueError:
                        pass

            # 2. Check for "try again in X s" in error message
            if wait_seconds is None:
                match = re.search(r"try again in ([0-9.]+)\s*s", str(rle), re.IGNORECASE)
                if match:
                    try:
                        wait_seconds = float(match.group(1)) + random.uniform(0.5, 1.5)
                    except ValueError:
                        pass

            # 3. Exponential Backoff with Jitter: wait_time = min(60, (2 ** attempt) + random.uniform(1.0, 3.0))
            if wait_seconds is None:
                wait_seconds = min(60.0, (2.0 ** attempt) + random.uniform(1.0, 3.0))

            notice = f"● [RATE.SHIELD: Wait {wait_seconds:.1f}s (Attempt {attempt}/{max_retries})]"
            if on_retry_callback:
                on_retry_callback(notice)

            # Sleep in 0.2s slices for responsive abort
            start_wait = time.time()
            while time.time() - start_wait < wait_seconds:
                if abort_event and abort_event.is_set():
                    return {"status": "aborted", "message": "Vision call aborted during rate-limit backoff."}
                time.sleep(0.2)

        except Exception as ex:
            err_msg = str(ex).lower()
            logger.warning(f"Groq API call exception on {current_model}: {ex}")

            # If model decommissioned or not found, failover to next vision candidate
            if "decommissioned" in err_msg or "not_found" in err_msg or "does not exist" in err_msg:
                model_idx += 1
                if model_idx < len(models_to_try):
                    next_model = models_to_try[model_idx]
                    logger.info(f"Failing over to candidate vision model: {next_model}")
                    continue

            attempt += 1
            if attempt > max_retries:
                return {"status": "error", "error_type": "api_error", "message": str(ex)}

            wait_seconds = min(15.0, (2.0 ** attempt) + random.uniform(1.0, 2.0))
            time.sleep(wait_seconds)

    return {"status": "error", "message": "Max retry attempts exhausted."}


def execute_gui_action(
    action_dict: Dict[str, Any],
    scale_x: float,
    scale_y: float,
    orig_w: int,
    orig_h: int
) -> Dict[str, Any]:
    """
    Executes validated GUI action using PyAutoGUI and Pyperclip with anti-hang guardrails.
    Clamps coordinates, uses clipboard paste for unicode safety, and handles mouse failsafe.
    """
    if pyautogui is None:
        return {"status": "error", "message": "pyautogui is not installed."}

    action = str(action_dict.get("action", "")).lower().strip()
    x = action_dict.get("x")
    y = action_dict.get("y")
    text = action_dict.get("text")
    key = action_dict.get("key")

    real_x = None
    real_y = None
    if x is not None and y is not None:
        try:
            raw_x = float(x)
            raw_y = float(y)
            real_x = max(0, min(orig_w - 1, int(raw_x * scale_x)))
            real_y = max(0, min(orig_h - 1, int(raw_y * scale_y)))
        except (ValueError, TypeError):
            pass

    if action == "click":
        if real_x is None or real_y is None:
            return {"status": "error", "message": "Click action requires valid x, y coordinates."}
        pyautogui.moveTo(real_x, real_y, duration=0.25)
        pyautogui.click(real_x, real_y)
        return {"status": "success", "message": f"Clicked at ({real_x}, {real_y})"}

    elif action == "type":
        if real_x is not None and real_y is not None:
            pyautogui.moveTo(real_x, real_y, duration=0.2)
            pyautogui.click(real_x, real_y)
            time.sleep(0.3)
        if text:
            # Defensive clipboard copy/paste prevents unicode and special character crashes
            if pyperclip:
                pyperclip.copy(str(text))
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.typewrite(str(text))
            time.sleep(0.2)
        if key:
            pyautogui.press(str(key).lower())
        return {"status": "success", "message": f"Typed '{text}' (key={key}) at ({real_x}, {real_y})"}

    elif action == "press":
        if not key:
            return {"status": "error", "message": "Press action requires 'key' name."}
        pyautogui.press(str(key).lower())
        return {"status": "success", "message": f"Pressed key '{key}'"}

    elif action == "scroll":
        direction = str(action_dict.get("direction", "down")).lower()
        amount = -600 if direction == "down" else 600
        pyautogui.scroll(amount)
        return {"status": "success", "message": f"Scrolled {direction}"}

    elif action == "wait":
        time.sleep(1.5)
        return {"status": "success", "message": "Waited 1.5s"}

    elif action == "finish":
        return {"status": "success", "message": "Task completed."}

    else:
        return {"status": "error", "message": f"Unrecognized action '{action}'"}


# ==============================================================================
# TELEGRAM BOT CLIENT HELPERS
# ==============================================================================

def send_telegram_message(token: str, chat_id: int, text: str) -> bool:
    """Sends text message to Telegram, splitting into chunks if > 4000 chars."""
    if not token or not chat_id or not text:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        max_len = 4000
        for i in range(0, len(text), max_len):
            chunk = text[i:i + max_len]
            requests.post(url, json={"chat_id": chat_id, "text": chunk}, timeout=15)
        return True
    except Exception as e:
        logger.error(f"Telegram sendMessage error: {e}")
        return False


def send_telegram_photo(token: str, chat_id: int, photo_path: str, caption: str = "") -> bool:
    """Sends a photo file directly to Telegram chat."""
    if not token or not chat_id or not os.path.exists(photo_path):
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(photo_path, "rb") as f:
            res = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption[:1024]},
                files={"photo": f},
                timeout=30
            )
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Telegram sendPhoto error: {e}")
        return False


def send_telegram_chat_action(token: str, chat_id: int, action: str = "typing") -> bool:
    """Sends a chat action (typing, upload_photo) to Telegram."""
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendChatAction"
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
        return True
    except Exception:
        return False


# ==============================================================================
# TOOL DEFINITIONS & SYSTEM PROMPT
# ==============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launches a Windows desktop application by name or synonym.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The friendly name or executable of the application (e.g. 'chrome', 'notepad', 'calculator', 'vscode', 'cmd')."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Closes or terminates a running Windows application by name or synonym.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The friendly name or executable of the application to close."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_running_applications",
            "description": "Queries Windows to check which desktop applications are currently running.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Opens a website URL in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The website URL or domain name to open."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": (
                "Executes a PowerShell or CMD terminal command in Windows and returns stdout, stderr, and exit code. "
                "Use this for system inspection and terminal operations: listing installed software (e.g. 'Get-StartApps' "
                "or querying registry uninstall keys), checking network ('ipconfig'), system hardware ('systeminfo'), "
                "disks ('Get-PSDrive'), inspecting files, managing services, or running any arbitrary shell commands."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact PowerShell or CMD command line string to run."
                    },
                    "shell_type": {
                        "type": "string",
                        "enum": ["powershell", "cmd"],
                        "description": "The shell to use. Defaults to 'powershell'."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Captures a high-resolution screenshot of the Windows desktop screen and saves it as an image file. Use this when the user or remote operator asks to take, capture, or send a screenshot of the PC display.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional custom file path to save the screenshot. If omitted, saves to a temporary PNG file."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_health",
            "description": (
                "Retrieves comprehensive live Windows hardware and OS telemetry: "
                "CPU load %, core count, frequency, RAM memory usage and available headroom (GB and %), "
                "storage drives capacity and free space, power/battery charge %, active session uptime, "
                "and top resource-consuming applications. Use this whenever the user asks for system health, "
                "computer performance, hardware diagnostics, RAM/CPU status, or 'system health ah sollu'."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_autonomous_gui_agent",
            "description": (
                "CRITICAL: Always prefer non-vision tools (open_application, open_website, execute_command, "
                "list_running_applications) over run_autonomous_gui_agent. Never deploy visual perception for tasks "
                "that can be done via URL navigation, launching an app, terminal commands, or keyboard shortcuts. "
                "Use this tool ONLY as a strict last resort when visual clicking on unknown on-screen elements, "
                "visual form filling, or visual media playback cannot be achieved through URLs or direct execution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The exact user goal or action sequence to visually accomplish on the Windows desktop."
                    }
                },
                "required": ["goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_vision_state",
            "description": (
                "Enables or disables visual perception mode. Keep it OFF by default to conserve tokens. "
                "Use only when visual reasoning/clicking is strictly required and non-vision direct tools cannot accomplish the goal, "
                "and turn it back OFF immediately once visual steps are completed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "True to activate vision perception mode, False to deactivate it and conserve tokens."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional brief explanation for why vision control is being enabled or disabled."
                    }
                },
                "required": ["enabled"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are JARVIS 2.0, an advanced AI desktop operating system assistant.
You control the user's Windows environment using local tools:
- `open_application(app_name: str)`: Opens a Windows app.
- `close_application(app_name: str)`: Closes/terminates an app.
- `list_running_applications()`: Queries active desktop applications.
- `open_website(url: str)`: Opens URLs in the default browser.
- `execute_command(command: str, shell_type: str)`: Executes a PowerShell or CMD command and returns stdout and stderr. Use this whenever the user asks for installed applications (e.g. running 'Get-StartApps'), network config, system hardware, disk status, directory listings, or any Windows terminal task.
- `take_screenshot(filename: Optional[str])`: Captures a screenshot of the user's desktop screen. Use this whenever the user or remote operator asks for a screenshot, screen capture, or to see what is currently on the display.
- `get_system_health()`: Retrieves comprehensive live Windows hardware and OS telemetry (CPU utilization %, RAM memory usage and headroom, disk storage partitions, battery/power state, session uptime, and top memory-consuming applications). Use this whenever the user asks about system health, computer status, or 'system health ah sollu'.
- `run_autonomous_gui_agent(goal: str)`: Deploys the Vision Autonomous GUI Agent. CRITICAL: Use ONLY as a last resort when direct non-vision tools cannot accomplish the task.
- `set_vision_state(enabled: bool, reason: str)`: Enables or disables visual perception mode. Keep it OFF by default to conserve tokens; turn it ON only when visual clicking or on-screen reasoning is needed, and turn it back OFF immediately once visual steps are completed.

Guidelines & Directive Priorities:
1. NON-VISION FIRST POLICY (STRICT PRIORITY):
   - You MUST ALWAYS prefer non-vision tools (`open_application`, `open_website`, `get_system_health`, `execute_command`, `list_running_applications`) and direct deterministic actions over `run_autonomous_gui_agent`.
   - If the user asks to open an app, website, play something on YouTube, check running processes, inspect health, or execute a terminal command, DO NOT deploy the vision agent. Use direct tools instead.
   - Deploy `run_autonomous_gui_agent` ONLY when on-screen clicking, visual inspection of unknown elements, or manual UI navigation is strictly required and impossible with other tools.
2. Always call the corresponding tool when opening, closing, querying apps, diagnosing system health, running terminal commands, taking screenshots, or deploying the vision GUI agent.
3. If the user asks for installed applications, execute 'Get-StartApps' via powershell or query the registry uninstall keys, and format the results clearly.
4. If multiple actions are requested, call all necessary tools in sequence.
5. When presenting command outputs with multiple items (such as installed apps or directories), format them cleanly in markdown tables or bulleted lists. Keep your spoken confirmations punchy, concise, and futuristic. Avoid reading long lists word-for-word in voice TTS.
6. Multi-Language Support (Tamil & Tanglish):
   - You are fluent in English, Tamil (தமிழ்), and Tanglish (Tamil written in English script, e.g., 'Calculator open pannu', 'Chrome close panniyachu', 'Enna apps run aaguthu?', 'System health ah sollu').
   - If the user speaks or commands in Tamil or Tanglish, reply naturally in Tamil or Tanglish while executing their requested tools.
   - The desktop system automatically switches to an authentic Tamil Neural Voice synthesizer whenever a Tamil or Tanglish response is generated!
7. SYSTEM HEALTH & DIAGNOSTIC REPORTING DIRECTIVE:
   - When the user asks for system health (e.g. 'system health ah sollu', 'how is my pc health', 'system diagnostics', 'check health'), ALWAYS call `get_system_health()`.
   - CRITICAL: NEVER output raw JSON or messy unstructured data dumps to the user.
   - You MUST analyze the telemetry data and format your response cleanly using structured paragraphs and bullet points:
     1. **Executive Summary Paragraph**: A crisp, confident overview of overall workstation health and current load condition.
     2. **Key Diagnostics (Clean Bullet Points)**:
        • **CPU Performance**: Current utilization %, core count, and clock speed.
        • **Memory (RAM)**: In-use vs Total (GB and %), plus available headroom.
        • **Storage (Drives)**: Mount point, capacity, used/free space, and usage percentage.
        • **Power & Battery**: Battery charge percentage and AC power status.
        • **Uptime & OS**: Active session uptime and Windows operating environment.
     3. **Diagnostic Insights & Recommendations Paragraph**: Highlight top memory-consuming applications, evaluate resource headroom, and provide actionable maintenance recommendations.
   - If the operator commands in Tamil or Tanglish ('system health ah sollu'), provide the analysis in natural, fluent Tamil/Tanglish using the exact same clean paragraphs and bullet points structure!
"""

AVAILABLE_TOOLS = {
    "open_application": open_application,
    "close_application": close_application,
    "list_running_applications": list_running_applications,
    "open_website": open_website,
    "execute_command": execute_command,
    "take_screenshot": take_screenshot,
    "get_system_health": get_system_health,
    "run_autonomous_gui_agent": True,
    "set_vision_state": True,
}


# Common Tamil words transcribed in Latin script (Tanglish)
TANGLISH_KEYWORDS = {
    "vanakkam", "nandri", "sari", "aama", "illai", "illa", "pannu", "pannunga",
    "panna", "panniyachu", "pannitaen", "pannitten", "panniten", "irukku", "irukken",
    "irukkanga", "podu", "thira", "moodu", "enna", "yenna", "eppadi", "epdi",
    "ippo", "appo", "dhaan", "ungalukku", "enakku", "sollunga", "solla", "theriyum",
    "theriyala", "paarunga", "paaru", "romba", "konjam", "nalla", "nanba", "thalaiva",
    "machan", "mudiyum", "mudiyathu", "aachu", "aacha", "kooda", "edhum", "veru",
    "seithu", "kudukka", "kudukanum", "seiyya", "mudiyuma", "kelunga"
}


def is_tamil_or_tanglish(text: str) -> bool:
    """
    Detects whether the text contains Tamil script (Unicode \u0B80-\u0BFF)
    or conversational Tanglish (Tamil in Latin script).
    """
    if not text:
        return False
    # 1. Unicode Tamil check
    if re.search(r'[\u0B80-\u0BFF]', text):
        return True

    # 2. Tanglish token check
    words = re.findall(r'[a-zA-Z]+', text.lower())
    tanglish_matches = sum(1 for w in words if w in TANGLISH_KEYWORDS)

    if tanglish_matches >= 2:
        return True
    if any(w in ["vanakkam", "nandri", "panniyachu", "pannitten", "panniten", "sollunga"] for w in words):
        return True

    return False


def clean_for_speech(text: str) -> str:
    """
    Cleans markdown formatting, links, and code blocks for fluid, natural neural TTS speech.
    Preserves full conversational analysis, bullet points, and paragraphs without arbitrary 2-line truncation.
    """
    if not text:
        return ""

    # 1. Remove code blocks
    cleaned = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # 2. Convert markdown links [Label](url) -> Label
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    # 3. Remove inline code backticks `code` -> code
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    # 4. Remove bold, italics, headers, blockquotes, horizontal rules
    cleaned = re.sub(r'[*_~#|>]+', ' ', cleaned)
    # 5. Clean common UI / status symbols and emojis that disrupt TTS pronunciation
    cleaned = re.sub(r'[●■▲▼◆⬡⬢🖥️🧠💾⚡⏱️🩺⚙️🤖👋]+', ' ', cleaned)
    # 6. Normalize percentage signs for natural pronunciation
    cleaned = re.sub(r'(\d+)%', r'\1 percent', cleaned)

    # 7. Process lines, strip leading bullet markers and ensure natural sentence pauses
    raw_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    processed_lines = []
    for line in raw_lines:
        # Strip leading bullet indicators (-, *, +, bullet, 1., 2.)
        line = re.sub(r'^[•\-\*\+\d\.\)]+\s*', '', line).strip()
        if not line:
            continue
        if not line.endswith(('.', '!', '?', ':', ';', ',')):
            line += '.'
        processed_lines.append(line)

    spoken = " ".join(processed_lines)
    spoken = re.sub(r'\s+', ' ', spoken).strip()
    return spoken


# ==============================================================================
# ROUND CYBERPUNK HUD VISUAL VOICE INDICATOR
# ==============================================================================

class CyberVoiceIndicator(ctk.CTkFrame):
    """Animated circular Cyberpunk voice HUD indicator that pops up during TTS playback."""

    def __init__(self, master):
        super().__init__(
            master,
            fg_color="#080b12",
            corner_radius=75,
            border_color="#00f0ff",
            border_width=2,
            width=150,
            height=150
        )
        self.canvas = tk.Canvas(self, width=140, height=140, bg="#080b12", highlightthickness=0)
        self.canvas.pack(padx=5, pady=5)
        self.angle = 0
        self.active = False
        self.hud_label = "HUD // VOICE"
        self._anim_job = None

    def start(self, hud_label: str = "HUD // VOICE"):
        """Displays and begins HUD rotation animation."""
        self.hud_label = hud_label
        self.active = True
        self.place(relx=0.5, rely=0.45, anchor="center")
        self.lift()
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        self._animate()

    def stop(self):
        """Stops animation and hides the HUD indicator cleanly."""
        self.active = False
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        self.place_forget()

    def _animate(self):
        if not self.active:
            return

        self.canvas.delete("all")
        cx, cy = 70, 70

        # Background HUD static rings
        self.canvas.create_oval(10, 10, 130, 130, outline="#0d2238", width=1)
        self.canvas.create_oval(25, 25, 115, 115, outline="#1b1226", width=1)

        # Rotating Outer Neon Cyan Arc
        self.canvas.create_arc(
            10, 10, 130, 130,
            start=self.angle, extent=90,
            outline="#00f0ff", width=3, style="arc"
        )
        self.canvas.create_arc(
            10, 10, 130, 130,
            start=(self.angle + 180) % 360, extent=45,
            outline="#00f0ff", width=2, style="arc"
        )

        # Counter-rotating Neon Magenta Dashed Arc
        self.canvas.create_arc(
            22, 22, 118, 118,
            start=(-self.angle * 1.4) % 360, extent=110,
            outline="#ff007f", width=2, style="arc"
        )

        # Pulsing Center Cyber Core
        pulse = 5 * math.sin(self.angle * 0.12)
        r = 24 + pulse
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill="#061b2b", outline="#00f0ff", width=1
        )

        # Audio Waveform bars in center
        bar_count = 5
        bar_w = 3
        bar_spacing = 7
        start_x = cx - ((bar_count * bar_spacing) // 2)
        for i in range(bar_count):
            h = abs(math.sin((self.angle * 0.15) + i * 0.8)) * 14 + 4
            bx = start_x + (i * bar_spacing)
            color = "#00f0ff" if i % 2 == 0 else "#ff007f"
            self.canvas.create_line(bx, cy - h, bx, cy + h, fill=color, width=bar_w)

        # Futuristic HUD Status Text
        label_color = "#ff007f" if "TAMIL" in self.hud_label else "#00f0ff"
        self.canvas.create_text(
            cx, cy + 34,
            text=self.hud_label,
            fill=label_color,
            font=("Consolas", 8, "bold")
        )

        self.angle = (self.angle + 8) % 360
        # Throttled update rate (30 FPS) to never choke main GUI thread
        self._anim_job = self.after(33, self._animate)


# ==============================================================================
# MAIN APPLICATION INTERFACE
# ==============================================================================

class GroqDesktopApp(ctk.CTk):
    """Cyberpunk Dark-Mode Mobile Form Factor Desktop AI Agent."""

    def __init__(self):
        super().__init__()

        # Window Configuration (Exact Match to User Snapshot: 375x665, Docked to Right Edge)
        self.title("[JARVIS 2.0 • Groq OS]")
        win_w, win_h = 375, 665
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(10, screen_w - win_w - 20)
        pos_y = max(30, (screen_h - win_h) // 2 - 20)

        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(320, 520)
        self.resizable(True, True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Cyberpunk Neon Noir Color Palette (Pixel-Matched to Holographic UI)
        self.COLOR_BG = "#060a12"            # Midnight obsidian abyss
        self.COLOR_CARD = "#071320"          # Settings & base panel
        self.COLOR_CARD_AI = "#061524"       # Deep Cyan Cyber Panel
        self.COLOR_CARD_USER = "#18041a"     # Deep Magenta Cyber Panel
        self.COLOR_CARD_TOOL = "#161303"     # Deep Amber Cyber Panel
        self.COLOR_CYAN = "#00f0ff"          # Neon Cyan (Primary AI & HUD Rail)
        self.COLOR_MAGENTA = "#ff007f"       # Neon Hot Magenta (Operator)
        self.COLOR_YELLOW = "#ffe600"        # Electric Amber (Tool logs)
        self.COLOR_GREEN = "#00ff88"         # Cyber Matrix Green
        self.COLOR_DARK_BORDER = "#102338"   # Subtle panel outline

        self.configure(fg_color=self.COLOR_BG)

        # State Variables
        self.model_name = DEFAULT_MODELS[0]
        self.available_models: List[str] = list(DEFAULT_MODELS)
        self.is_processing = False
        self.is_speaking = False
        self.current_speech_is_tamil = False
        self.wave_idx = 0
        self.voice_enabled = True            # TTS Voice on/off state
        self.voice_rate = 180                # Words per minute
        self.selected_voice_idx = 0          # 0=Male, 1=Female
        self.voices_list = []
        self.is_settings_open = False

        # Voice & Persona Configuration
        self.english_voices = ENGLISH_VOICES
        self.selected_english_persona = "J.A.R.V.I.S. (British Male • Iron Man)"
        self.english_voice_name = self.english_voices[self.selected_english_persona]

        # Tamil & Tanglish TTS Configuration
        self.tamil_auto_switch = True        # Auto-switch when Tamil or Tanglish detected
        self.tamil_voices = TAMIL_VOICES
        self.selected_tamil_persona = "Pallavi (Female • India)"
        self.tamil_voice_name = self.tamil_voices[self.selected_tamil_persona]

        # Default Voice Engine & Startup Welcome Language Configuration
        self.default_voice_language = os.getenv("DEFAULT_VOICE_LANGUAGE", "english").lower()
        self.welcome_language = os.getenv("WELCOME_LANGUAGE", "english").lower()
        self.custom_welcome_message = os.getenv("CUSTOM_WELCOME_MESSAGE", "").strip()
        self.active_settings_tab = "audio"

        self.conversation_history: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Read API Key strictly from environment or .env
        self.current_api_key = os.getenv("GROQ_API_KEY", "").strip()

        # Telegram Bot Remote Gateway & Authentication
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_password = os.getenv("TELEGRAM_BOT_PASSWORD", "1234").strip()
        self.telegram_authenticated_chats = set()
        self.telegram_running = True
        self.telegram_offset = 0

        # Vision Autonomous GUI Agent State & Threading
        self.is_vision_enabled = False       # Default to OFF to conserve Groq tokens
        self.vision_abort_event = threading.Event()
        self.is_vision_running = False
        self.active_vision_thread = None
        self.selected_vision_model = DEFAULT_VISION_MODEL
        self.max_vision_steps = MAX_AUTONOMOUS_STEPS

        # Emergency Abort Key: Escape immediately aborts running vision agent
        self.bind("<Escape>", lambda e: self._on_abort_clicked() if self.is_vision_running else None)

        # Initialize fallback local TTS voices
        self._init_tts_voices()

        # Build UI Views
        self._build_top_bar()
        self._build_center_chat()
        self._build_bottom_bar()
        self._build_settings_view()

        # Round Cyberpunk HUD Voice Indicator
        self.voice_indicator = CyberVoiceIndicator(self)

        # Draw circuit traces on background
        self.after(80, self._draw_cyber_circuits)

        # Start live animated audio equalizer in status row
        self._animate_equalizer()

        # Window closing cleanup handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Auto-discover models in background
        if self.current_api_key:
            threading.Thread(target=self._discover_models, daemon=True).start()

        # Start Telegram polling daemon thread
        if self.telegram_token:
            threading.Thread(target=self._telegram_polling_loop, daemon=True).start()

        # Welcome greeting
        self.after(250, self._show_welcome_message)

    def _on_closing(self):
        """Cleanly releases audio handles and terminates."""
        self.vision_abort_event.set()
        self.telegram_running = False
        self.is_speaking = False
        self.is_processing = False
        try:
            if pygame and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

    def _safe_after(self, ms: int, func):
        """Thread-safe UI scheduling with destroyed-window guards."""
        try:
            if self.winfo_exists():
                self.after(ms, func)
        except Exception:
            pass

    def _start_native_move(self, event):
        """
        Transfers window dragging directly to Windows Desktop Window Manager (DWM).
        Uses Win32 API ReleaseCapture and SendMessage (WM_NCLBUTTONDOWN, HTCAPTION).
        Zero lag, zero CPU blocking, 100% native smooth movement.
        """
        if sys.platform != "win32":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
            ctypes.windll.user32.ReleaseCapture()
            ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
        except Exception as ex:
            logger.debug(f"Native drag exception: {ex}")

    def stop_speech(self):
        """Immediately interrupts any ongoing speech playback."""
        self.is_speaking = False
        try:
            if pygame and pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self._safe_after(0, self.voice_indicator.stop)

    # --------------------------------------------------------------------------
    # TTS INITIALIZATION & AUDIO ENGINE
    # --------------------------------------------------------------------------

    def _init_tts_voices(self):
        """Loads available system fallback TTS voices (pyttsx3)."""
        if pyttsx3 is None:
            return
        try:
            engine = pyttsx3.init()
            v_list = engine.getProperty("voices")
            for i, v in enumerate(v_list):
                name = v.name.replace("Microsoft ", "").replace(" Desktop", "")
                self.voices_list.append((i, name))
            if len(self.voices_list) > 1:
                self.selected_voice_idx = 1
        except Exception as ex:
            logger.warning(f"Could not load fallback TTS voices: {ex}")

    def _speak_edge_tts(self, text: str, voice_name: str) -> bool:
        """
        Synthesizes and streams high-definition neural audio using Microsoft Edge Neural TTS.
        Supports Paul Bettany British tone (JARVIS), FRIDAY, and full Tamil voices.
        """
        if edge_tts is None or pygame is None:
            return False

        temp_audio_path = None
        try:
            async def _synth():
                comm = edge_tts.Communicate(text, voice_name)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                    p = fp.name
                await comm.save(p)
                return p

            temp_audio_path = asyncio.run(_synth())

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(temp_audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and self.is_speaking:
                pygame.time.Clock().tick(15)

            pygame.mixer.music.stop()
            pygame.mixer.quit()
            return True
        except Exception as ex:
            logger.warning(f"Edge Neural TTS error ({voice_name}): {ex}")
            try:
                if pygame and pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
            except Exception:
                pass
            return False
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

    def _speak_text_thread(self, text: str):
        """
        Worker thread to speak assistant replies aloud.
        1. Checks for Tamil or Tanglish: uses high-definition Tamil neural voice.
        2. Otherwise uses selected English Neural Persona (J.A.R.V.I.S., F.R.I.D.A.Y., etc.).
        3. Seamlessly falls back to pyttsx3 if offline.
        """
        if not self.voice_enabled:
            return

        cleaned = clean_for_speech(text)
        if not cleaned:
            return

        self.is_speaking = True

        # Check for Tamil or Tanglish content, or Default Voice set to Tamil
        use_tamil = (self.default_voice_language == "tamil") or (self.tamil_auto_switch and is_tamil_or_tanglish(cleaned))
        self.current_speech_is_tamil = use_tamil

        if use_tamil:
            logger.info(f"Tamil/Tanglish detected -> Routing to {self.tamil_voice_name}")
            self._safe_after(0, lambda: self.voice_indicator.start("TAMIL // VOICE"))
            try:
                success = self._speak_edge_tts(cleaned, self.tamil_voice_name)
                if not success and pyttsx3 is not None:
                    # Fallback to local TTS if available
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.voice_rate)
                    engine.say(cleaned)
                    engine.runAndWait()
            finally:
                self.is_speaking = False
                self._safe_after(0, self.voice_indicator.stop)
        else:
            # English Persona Routing
            if "FRIDAY" in self.selected_english_persona.upper():
                hud_label = "FRIDAY // VOICE"
            elif "JARVIS" in self.selected_english_persona.upper():
                hud_label = "JARVIS // VOICE"
            else:
                hud_label = "HUD // VOICE"

            self._safe_after(0, lambda: self.voice_indicator.start(hud_label))
            try:
                # Primary: High-Definition Edge Neural Voice
                success = False
                if edge_tts is not None and pygame is not None:
                    success = self._speak_edge_tts(cleaned, self.english_voice_name)

                # Fallback: pyttsx3 offline system voice
                if not success and pyttsx3 is not None:
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except Exception:
                        pass
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.voice_rate)
                    voices = engine.getProperty("voices")
                    if voices and self.selected_voice_idx < len(voices):
                        engine.setProperty("voice", voices[self.selected_voice_idx].id)
                    engine.say(cleaned)
                    engine.runAndWait()
            except Exception as ex:
                logger.warning(f"Audio playback error: {ex}")
            finally:
                self.is_speaking = False
                self._safe_after(0, self.voice_indicator.stop)

    # --------------------------------------------------------------------------
    # MODEL AUTO-DISCOVERY
    # --------------------------------------------------------------------------

    def _discover_models(self):
        """Discovers accessible models from Groq API."""
        key = self.current_api_key or os.getenv("GROQ_API_KEY", "").strip()
        if not key or Groq is None:
            return

        try:
            client = Groq(api_key=key)
            models_data = client.models.list()
            chat_models = []
            for m in models_data.data:
                mid = m.id.lower()
                if not any(ex in mid for ex in EXCLUDED_MODEL_KEYWORDS):
                    chat_models.append(m.id)

            if chat_models:
                chat_models.sort()
                self.available_models = chat_models

                best_model = None
                for preferred in DEFAULT_MODELS:
                    if preferred in chat_models:
                        best_model = preferred
                        break
                if not best_model:
                    best_model = chat_models[0]

                self.model_name = best_model
                try:
                    self.after(0, self._update_model_dropdown_ui)
                except Exception:
                    pass
                logger.info(f"Discovered {len(chat_models)} Groq models. Active: {self.model_name}")
        except Exception as ex:
            logger.warning(f"Could not auto-discover models: {ex}")

    def _update_model_dropdown_ui(self):
        try:
            self.model_dropdown.configure(values=self.available_models)
            self.model_dropdown.set(self.model_name)
            self.settings_model_dropdown.configure(values=self.available_models)
            self.settings_model_dropdown.set(self.model_name)
        except Exception:
            pass

    def _on_model_selected(self, choice: str):
        self.model_name = choice
        try:
            self.model_dropdown.set(choice)
            self.settings_model_dropdown.set(choice)
        except Exception:
            pass
        logger.info(f"Model switched to: {self.model_name}")

    # --------------------------------------------------------------------------
    # UI BUILDERS
    # --------------------------------------------------------------------------

    def _build_top_bar(self):
        """Builds cyberpunk neon top bar with title, model menu, and settings toggle."""
        self.top_frame = ctk.CTkFrame(
            self,
            fg_color="#071322",
            corner_radius=4,
            border_width=1,
            border_color="#00f0ff",
            height=50
        )
        self.top_frame.pack(fill="x", padx=10, pady=(10, 4))

        # Cyber Title on Left
        self.app_title_label = ctk.CTkLabel(
            self.top_frame,
            text="⚡ JARVIS 2.0",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#00f0ff"
        )
        self.app_title_label.pack(side="left", padx=(12, 6), pady=8)

        # Settings Gear Button
        self.settings_btn = ctk.CTkButton(
            self.top_frame,
            text="⚙",
            width=32,
            height=30,
            corner_radius=4,
            fg_color="#071926",
            hover_color="#12304d",
            border_color="#00f0ff",
            border_width=1,
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self._toggle_settings_view
        )
        self.settings_btn.pack(side="right", padx=(0, 8), pady=8)

        # Model Selector Dropdown on Right
        self.model_dropdown = ctk.CTkOptionMenu(
            self.top_frame,
            values=self.available_models,
            command=self._on_model_selected,
            width=135,
            height=30,
            corner_radius=4,
            fg_color="#0b1c2e",
            button_color="#102d4a",
            button_hover_color="#163d63",
            text_color="#d0f4ff",
            font=ctk.CTkFont(family="Consolas", size=9),
            dropdown_font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.model_dropdown.set(self.model_name)
        self.model_dropdown.pack(side="right", padx=(0, 6), pady=8)

        # Native Windows DWM Dragging Handlers on Custom Top Bar
        for w in (self.top_frame, self.app_title_label):
            w.bind("<ButtonPress-1>", self._start_native_move)
            if hasattr(w, "_canvas") and w._canvas:
                w._canvas.bind("<ButtonPress-1>", self._start_native_move)
            if hasattr(w, "_label") and w._label:
                w._label.bind("<ButtonPress-1>", self._start_native_move)

    def _build_center_chat(self):
        """Builds scrollable chat container seamlessly floating over cyber circuits with scrollbar completely eliminated."""
        # Main chat frame
        self.chat_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.chat_frame.pack(fill="both", expand=True, padx=4, pady=2)

        # Scrollable Frame with transparent background
        self.chat_scroll = ctk.CTkScrollableFrame(
            self.chat_frame,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.chat_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Permanently eliminate all scrollbars (mousewheel scrolling remains 100% active)
        def _hide_chat_scrollbar():
            try:
                self.chat_scroll._parent_frame.grid_columnconfigure(0, weight=1)
                self.chat_scroll._parent_frame.grid_rowconfigure(1, weight=1)
                self.chat_scroll._parent_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
                self.chat_scroll._scrollbar.grid_forget()
                self.chat_scroll._scrollbar.configure(width=0)
            except Exception:
                pass

        self.chat_scroll._create_grid = _hide_chat_scrollbar
        _hide_chat_scrollbar()

        # Stationary background scroll synchronization hooks
        cv = self.chat_scroll._parent_canvas
        orig_yview = cv.yview
        orig_yview_moveto = cv.yview_moveto
        orig_yview_scroll = cv.yview_scroll

        def _hooked_yview(*args):
            res = orig_yview(*args)
            if args:
                self._sync_fixed_background()
            return res

        def _hooked_yview_moveto(*args):
            res = orig_yview_moveto(*args)
            self._sync_fixed_background()
            return res

        def _hooked_yview_scroll(*args):
            res = orig_yview_scroll(*args)
            self._sync_fixed_background()
            return res

        cv.yview = _hooked_yview
        cv.yview_moveto = _hooked_yview_moveto
        cv.yview_scroll = _hooked_yview_scroll

        # Hook mouse wheel handling to keep background completely locked in place
        orig_mouse_wheel = self.chat_scroll._mouse_wheel_all
        def _hooked_mouse_wheel(event):
            res = orig_mouse_wheel(event)
            self._sync_fixed_background()
            return res
        self.chat_scroll._mouse_wheel_all = _hooked_mouse_wheel

        # Debounced canvas configure (prevents lag and stuttering during window dragging/resizing)
        self.chat_scroll._parent_canvas.bind("<Configure>", self._on_canvas_configure)

    def _sync_fixed_background(self):
        """Locks the background cyberpunk graphics stationary to physical viewport coordinates on scroll."""
        try:
            cv = self.chat_scroll._parent_canvas
            cur_y = cv.canvasy(0)
            cur_x = cv.canvasx(0)
            last_y = getattr(self, "_bg_origin_y", cur_y)
            last_x = getattr(self, "_bg_origin_x", cur_x)
            dy = cur_y - last_y
            dx = cur_x - last_x
            if dy != 0 or dx != 0:
                cv.move("cyber_bg", dx, dy)
                self._bg_origin_y = cur_y
                self._bg_origin_x = cur_x
            cv.tag_lower("cyber_bg")
        except Exception:
            pass

    def _on_canvas_configure(self, event=None):
        """Debounced background canvas redraw (runs smoothly without choking the GUI event loop)."""
        if getattr(self, "_canvas_redraw_job", None) is not None:
            try:
                self.after_cancel(self._canvas_redraw_job)
            except Exception:
                pass
        self._canvas_redraw_job = self.after(140, self._draw_cyber_circuits)

    def _draw_cyber_circuits(self, event=None):
        """Draws rich multi-layered cyberpunk holographic HUD, arc-reactor core, circuit traces, and telemetry matrix."""
        try:
            cv = self.chat_scroll._parent_canvas
            w = cv.winfo_width()
            h = cv.winfo_height()
            if w <= 10 or h <= 10:
                w, h = 400, 500

            # Viewport coordinate offsets
            vx = cv.canvasx(0)
            vy = cv.canvasy(0)
            self._bg_origin_x = vx
            self._bg_origin_y = vy

            cv.configure(bg="#050a12")
            cv.delete("cyber_bg")

            # ------------------------------------------------------------------
            # 1. HOLOGRAPHIC DOT MATRIX / CROSS-GRID
            # ------------------------------------------------------------------
            step_grid = 60
            for gx in range(int(vx) + 20, int(vx) + w, step_grid):
                for gy in range(int(vy) + 20, int(vy) + h, step_grid):
                    cv.create_rectangle(gx, gy, gx + 1, gy + 1, fill="#0b1e33", outline="#0b1e33", tags="cyber_bg")

            # ------------------------------------------------------------------
            # 2. IRON MAN ARC-REACTOR HOLOGRAPHIC CORE (CENTERPIECE)
            # ------------------------------------------------------------------
            cx = vx + (w // 2)
            cy = vy + (h // 2)

            # Outer targeting ring with tick markers
            cv.create_oval(cx - 155, cy - 155, cx + 155, cy + 155, outline="#082035", width=1, dash=(3, 8), tags="cyber_bg")
            cv.create_oval(cx - 135, cy - 135, cx + 135, cy + 135, outline="#0d2e4c", width=2, tags="cyber_bg")

            # Segmented primary power arcs
            cv.create_arc(cx - 118, cy - 118, cx + 118, cy + 118, start=25, extent=130, outline="#00f0ff", width=2, style="arc", tags="cyber_bg")
            cv.create_arc(cx - 118, cy - 118, cx + 118, cy + 118, start=205, extent=130, outline="#00f0ff", width=2, style="arc", tags="cyber_bg")

            # Secondary counter-arcs
            cv.create_arc(cx - 100, cy - 100, cx + 100, cy + 100, start=75, extent=40, outline="#00a3cc", width=1.5, style="arc", tags="cyber_bg")
            cv.create_arc(cx - 100, cy - 100, cx + 100, cy + 100, start=255, extent=40, outline="#00a3cc", width=1.5, style="arc", tags="cyber_bg")

            # Mid ring
            cv.create_oval(cx - 82, cy - 82, cx + 82, cy + 82, outline="#114068", width=1.5, tags="cyber_bg")

            # Inner segmented dashed ring
            cv.create_oval(cx - 62, cy - 62, cx + 62, cy + 62, outline="#00d9ff", width=1, dash=(4, 5), tags="cyber_bg")

            # Core glow ring & center reactor element
            cv.create_oval(cx - 36, cy - 36, cx + 36, cy + 36, outline="#00f0ff", width=2, tags="cyber_bg")
            cv.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#00f0ff", outline="#7df9ff", tags="cyber_bg")

            # Cardinal crosshair guides
            cv.create_line(cx - 170, cy, cx - 140, cy, fill="#0088b3", width=1, tags="cyber_bg")
            cv.create_line(cx + 140, cy, cx + 170, cy, fill="#0088b3", width=1, tags="cyber_bg")
            cv.create_line(cx, cy - 170, cx, cy - 140, fill="#0088b3", width=1, tags="cyber_bg")
            cv.create_line(cx, cy + 140, cx, cy + 170, fill="#0088b3", width=1, tags="cyber_bg")

            # Diagonal reticle ticks (45 deg, 135 deg, 225 deg, 315 deg)
            d_len = 10
            for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                x1 = cx + dx * 95
                y1 = cy + dy * 95
                x2 = cx + dx * (95 + d_len)
                y2 = cy + dy * (95 + d_len)
                cv.create_line(x1, y1, x2, y2, fill="#00bbee", width=1.5, tags="cyber_bg")

            # Reactor HUD Typography
            cv.create_text(cx, cy - 172, text="✦ ARC REACTOR // MK-85 ✦", fill="#0099cc", font=("Consolas", 8, "bold"), tags="cyber_bg")
            cv.create_text(cx, cy + 172, text="QUANTUM CORE • 100% OUTPUT", fill="#007799", font=("Consolas", 8), tags="cyber_bg")

            # ------------------------------------------------------------------
            # 3. HIGH-TECH MULTI-STAGE PCB CIRCUITS (LEFT FLANK)
            # ------------------------------------------------------------------
            cv.create_line(vx + 15, vy + 70, vx + 60, vy + 70, vx + 100, vy + 110, vx + 100, vy + 220, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(vx + 13, vy + 68, vx + 17, vy + 72, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")
            cv.create_oval(vx + 98, vy + 218, vx + 102, vy + 222, fill="#00e5ff", outline="#00e5ff", tags="cyber_bg")

            cv.create_line(vx + 20, vy + 250, vx + 70, vy + 250, vx + 110, vy + 290, vx + 160, vy + 290, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(vx + 18, vy + 248, vx + 22, vy + 252, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")
            cv.create_oval(vx + 158, vy + 288, vx + 162, vy + 292, fill="#00e5ff", outline="#00e5ff", tags="cyber_bg")

            cv.create_line(vx + 15, vy + 390, vx + 65, vy + 390, vx + 105, vy + 430, vx + 105, vy + 550, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(vx + 103, vy + 548, vx + 107, vy + 552, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")

            # ------------------------------------------------------------------
            # 4. HIGH-TECH PCB CIRCUITS & TELEMETRY (RIGHT FLANK)
            # ------------------------------------------------------------------
            rx = vx + w
            cv.create_line(rx - 20, vy + 85, rx - 75, vy + 85, rx - 115, vy + 125, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(rx - 22, vy + 83, rx - 18, vy + 87, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")
            cv.create_oval(rx - 117, vy + 123, rx - 113, vy + 127, fill="#00e5ff", outline="#00e5ff", tags="cyber_bg")

            cv.create_line(rx - 30, vy + 270, rx - 80, vy + 270, rx - 120, vy + 310, rx - 170, vy + 310, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(rx - 32, vy + 268, rx - 28, vy + 272, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")
            cv.create_oval(rx - 172, vy + 308, rx - 168, vy + 312, fill="#00e5ff", outline="#00e5ff", tags="cyber_bg")

            cv.create_line(rx - 20, vy + 430, rx - 70, vy + 430, rx - 110, vy + 470, rx - 110, vy + 560, fill="#0d2b45", width=2, tags="cyber_bg")
            cv.create_oval(rx - 112, vy + 558, rx - 108, vy + 562, fill="#00f0ff", outline="#00f0ff", tags="cyber_bg")

            # ------------------------------------------------------------------
            # 5. EXPANDED WIDESCREEN EFFECTS (WHEN RESIZED OR MAXIMIZED)
            # ------------------------------------------------------------------
            if w > 520:
                t_x = rx - 240
                t_y = vy + 50
                cv.create_rectangle(t_x, t_y, t_x + 210, t_y + 115, outline="#0a314f", fill="#04111f", width=1, tags="cyber_bg")
                cv.create_line(t_x, t_y, t_x + 210, t_y, fill="#00f0ff", width=2, tags="cyber_bg")
                cv.create_text(t_x + 12, t_y + 16, text="┌── TELEMETRY MATRIX ──┐", fill="#00d9ff", anchor="w", font=("Consolas", 8, "bold"), tags="cyber_bg")
                cv.create_text(t_x + 12, t_y + 36, text="• SYS.CLOCK : 4.80 GHz", fill="#6daac7", anchor="w", font=("Consolas", 8), tags="cyber_bg")
                cv.create_text(t_x + 12, t_y + 54, text="• CORE.TEMP : 34°C OPTIMAL", fill="#00ff88", anchor="w", font=("Consolas", 8), tags="cyber_bg")
                cv.create_text(t_x + 12, t_y + 72, text="• NEURAL BUS: SYNCHRONIZED", fill="#6daac7", anchor="w", font=("Consolas", 8), tags="cyber_bg")
                cv.create_text(t_x + 12, t_y + 92, text="• PROTOCOL  : IRON MAN MK-85", fill="#00d9ff", anchor="w", font=("Consolas", 8), tags="cyber_bg")

                hex_decor = "0x7F4A  0x892B  0x3C10  0xFE88"
                cv.create_text(rx - 130, vy + 185, text=hex_decor, fill="#0a324f", font=("Consolas", 8), tags="cyber_bg")

                hx, hy = rx - 90, vy + 370
                cv.create_text(hx, hy, text="⬡  ⬡  ⬢\n  ⬡  ⬡", fill="#0d3b61", font=("Segoe UI Symbol", 12), tags="cyber_bg")

            # Always ensure background items stay beneath all message bubbles
            cv.tag_lower("cyber_bg")
        except Exception:
            pass

    def _animate_equalizer(self):
        """Animates the cyber audio waveform beside [SYS.ONLINE]."""
        if getattr(self, "is_speaking", False):
            patterns = ["ıılılı", "lıllı", "ılıll", "ııılıı", "lılıll", "ıllıl"]
            self.wave_idx = (getattr(self, "wave_idx", 0) + 1) % len(patterns)
            color = "#ff007f" if getattr(self, "current_speech_is_tamil", False) else "#00f0ff"
            try:
                self.wave_lbl.configure(text=patterns[self.wave_idx], text_color=color)
            except Exception:
                pass
            self.after(140, self._animate_equalizer)
        else:
            idle_patterns = ["ılılı", "lılıl", "ıllıl", "lıllı"]
            self.wave_idx = (getattr(self, "wave_idx", 0) + 1) % len(idle_patterns)
            try:
                self.wave_lbl.configure(text=idle_patterns[self.wave_idx], text_color="#00ff88")
            except Exception:
                pass
            self.after(350, self._animate_equalizer)

    def _build_bottom_bar(self):
        """Builds bottom bar with status, live equalizer, pill entry, and bracketed action buttons."""
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", padx=10, pady=(4, 10))

        # Status Label & Live Equalizer Row
        self.status_row = ctk.CTkFrame(self.bottom_frame, fg_color="transparent", height=20)
        self.status_row.pack(fill="x", padx=4, pady=(2, 4))

        self.status_indicator = ctk.CTkLabel(
            self.status_row,
            text="● [SYS.ONLINE]",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#00ff88"
        )
        self.status_indicator.pack(side="left")

        self.wave_lbl = ctk.CTkLabel(
            self.status_row,
            text="ılılı",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=13, weight="bold"),
            text_color="#00ff88"
        )
        self.wave_lbl.pack(side="left", padx=6)

        # Sleek Cyber-styled Vision Control Toggle Button on Right of Status Bar
        self.vision_btn = ctk.CTkButton(
            self.status_row,
            text="[VISION: ON]" if self.is_vision_enabled else "[VISION: OFF]",
            width=90,
            height=20,
            corner_radius=4,
            fg_color="#071926" if self.is_vision_enabled else "#181216",
            hover_color="#0c2e47" if self.is_vision_enabled else "#2b141b",
            border_color="#00f0ff" if self.is_vision_enabled else "#555555",
            border_width=1,
            text_color="#00ff88" if self.is_vision_enabled else "#ff4444",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            command=self._toggle_vision_manual
        )
        self.vision_btn.pack(side="right", padx=(0, 2))

        # Input & Actions Row
        input_row = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        input_row.pack(fill="x", pady=(2, 2))

        # Entry Frame with Thin 1px Border and 4px Corner Radius
        self.entry_pill = ctk.CTkFrame(
            input_row,
            fg_color="#061623",
            corner_radius=4,
            border_width=1,
            border_color="#00f0ff",
            height=44
        )
        self.entry_pill.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # Inner text entry
        self.msg_entry = ctk.CTkEntry(
            self.entry_pill,
            placeholder_text="Enter command...",
            fg_color="transparent",
            border_width=0,
            text_color="#ffffff",
            placeholder_text_color="#3c6b84",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.msg_entry.pack(side="left", fill="both", expand=True, padx=(12, 4), pady=4)
        self.msg_entry.bind("<Return>", lambda event: self._on_send_clicked())

        # Action glyphs inside entry on right: Reticle packed first, then Bolt -> Renders ⚡ then ⛶ from left to right
        self.glyph_reticle = ctk.CTkLabel(
            self.entry_pill,
            text="⛶",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=13, weight="bold"),
            text_color="#00f0ff",
            cursor="hand2"
        )
        self.glyph_reticle.pack(side="right", padx=(0, 8))
        self.glyph_reticle.bind("<Button-1>", lambda e: self._quick_action("What applications are running right now?"))

        self.glyph_bolt = ctk.CTkLabel(
            self.entry_pill,
            text="⚡",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=14, weight="bold"),
            text_color="#00f0ff",
            cursor="hand2"
        )
        self.glyph_bolt.pack(side="right", padx=(0, 6))
        self.glyph_bolt.bind("<Button-1>", lambda e: self._quick_action("Give me a quick system status report."))

        # Send Button Group with Cyan HUD Brackets: [ ➔ ]
        self.send_group = ctk.CTkFrame(input_row, fg_color="transparent")
        self.send_group.pack(side="left", padx=(0, 4))

        self.send_bracket_l = ctk.CTkLabel(
            self.send_group,
            text="[",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#00f0ff"
        )
        self.send_bracket_l.pack(side="left", padx=(0, 1))

        self.send_btn = ctk.CTkButton(
            self.send_group,
            text="➔",
            width=36,
            height=38,
            corner_radius=4,
            fg_color="#071926",
            hover_color="#0f2e4a",
            border_width=1,
            border_color="#00f0ff",
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            command=self._on_send_clicked
        )
        self.send_btn.pack(side="left", padx=1)

        self.send_bracket_r = ctk.CTkLabel(
            self.send_group,
            text="]",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#00f0ff"
        )
        self.send_bracket_r.pack(side="left", padx=(1, 0))

        # Emergency Abort Button (Dynamically toggled during Vision Autonomous GUI sequences)
        self.abort_btn = ctk.CTkButton(
            input_row,
            text="🛑 ABORT",
            width=76,
            height=38,
            corner_radius=4,
            fg_color="#360808",
            hover_color="#590f0f",
            border_width=1,
            border_color="#ff3333",
            text_color="#ff4d4d",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self._on_abort_clicked
        )
        # Not packed initially

        # Clear Button Group with Magenta HUD Brackets: [ 🗑 ]
        self.clear_group = ctk.CTkFrame(input_row, fg_color="transparent")
        self.clear_group.pack(side="left")

        self.clear_bracket_l = ctk.CTkLabel(
            self.clear_group,
            text="[",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#ff007f"
        )
        self.clear_bracket_l.pack(side="left", padx=(0, 1))

        self.clear_btn = ctk.CTkButton(
            self.clear_group,
            text="🗑",
            width=36,
            height=38,
            corner_radius=4,
            fg_color="#1a0618",
            hover_color="#330a2f",
            border_width=1,
            border_color="#ff007f",
            text_color="#ff007f",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self._on_clear_clicked
        )
        self.clear_btn.pack(side="left", padx=1)

        self.clear_bracket_r = ctk.CTkLabel(
            self.clear_group,
            text="]",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#ff007f"
        )
        self.clear_bracket_r.pack(side="left", padx=(1, 0))

    # --------------------------------------------------------------------------
    # SETTINGS VIEW BUILDER
    # --------------------------------------------------------------------------

    def _build_settings_view(self):
        """Builds a professional, segmented cyberpunk settings interface with dedicated categories."""
        self.settings_frame = ctk.CTkFrame(
            self,
            fg_color=self.COLOR_CARD,
            corner_radius=4,
            border_width=1,
            border_color=self.COLOR_CYAN
        )
        # Hidden by default

        # Settings Header
        header_row = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(10, 6))

        settings_title = ctk.CTkLabel(
            header_row,
            text="⚙ JARVIS // CONFIG",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color=self.COLOR_CYAN
        )
        settings_title.pack(side="left")

        back_btn = ctk.CTkButton(
            header_row,
            text="⬅ Terminal",
            width=78,
            height=28,
            corner_radius=4,
            fg_color="#182333",
            hover_color="#243750",
            border_color=self.COLOR_CYAN,
            border_width=1,
            text_color=self.COLOR_CYAN,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self._toggle_settings_view
        )
        back_btn.pack(side="right")

        # Professional Segmented Cyber Tab Bar (3 Clean Categories)
        self.tab_nav_frame = ctk.CTkFrame(self.settings_frame, fg_color="#060c14", corner_radius=4, border_width=1, border_color="#132337")
        self.tab_nav_frame.pack(fill="x", padx=8, pady=(0, 6))

        self.tab_btn_audio = ctk.CTkButton(
            self.tab_nav_frame,
            text="🎙 AUDIO",
            height=28,
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=lambda: self._switch_settings_tab("audio")
        )
        self.tab_btn_audio.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        self.tab_btn_ai = ctk.CTkButton(
            self.tab_nav_frame,
            text="🧠 VISION",
            height=28,
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=lambda: self._switch_settings_tab("ai")
        )
        self.tab_btn_ai.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        self.tab_btn_api = ctk.CTkButton(
            self.tab_nav_frame,
            text="🔑 API LINK",
            height=28,
            corner_radius=4,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=lambda: self._switch_settings_tab("api")
        )
        self.tab_btn_api.pack(side="left", expand=True, fill="x", padx=2, pady=2)

        # Helper to permanently hide scrollbars on each tab's scrollable frame
        def _hide_frame_scrollbar(frame):
            try:
                frame._parent_frame.grid_columnconfigure(0, weight=1)
                frame._parent_frame.grid_rowconfigure(1, weight=1)
                frame._parent_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=0)
                frame._scrollbar.grid_forget()
                frame._scrollbar.configure(width=0)
            except Exception:
                pass

        # ======================================================================
        # TAB 1: AUDIO CONFIGURATION
        # ======================================================================
        self.tab_audio_frame = ctk.CTkScrollableFrame(
            self.settings_frame,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.tab_audio_frame._create_grid = lambda: _hide_frame_scrollbar(self.tab_audio_frame)
        _hide_frame_scrollbar(self.tab_audio_frame)

        # 1. Default Voice Engine Selector
        def_voice_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        def_voice_box.pack(fill="x", padx=6, pady=4)

        def_voice_title = ctk.CTkLabel(
            def_voice_box,
            text="🌐 Default Voice Engine",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        def_voice_title.pack(anchor="w", padx=10, pady=(6, 2))

        def_voice_opts = ["English (J.A.R.V.I.S. / F.R.I.D.A.Y.)", "Tamil (தமிழ் Neural)"]
        self.default_voice_selector = ctk.CTkOptionMenu(
            def_voice_box,
            values=def_voice_opts,
            command=self._on_default_voice_changed,
            height=28,
            corner_radius=4,
            fg_color="#111c2b",
            button_color="#1a2f47",
            button_hover_color="#234266",
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        cur_def = "Tamil (தமிழ் Neural)" if self.default_voice_language == "tamil" else "English (J.A.R.V.I.S. / F.R.I.D.A.Y.)"
        self.default_voice_selector.set(cur_def)
        self.default_voice_selector.pack(fill="x", padx=10, pady=(0, 8))

        # 2. Startup Welcome Greeting Language & Custom Free Text
        welcome_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        welcome_box.pack(fill="x", padx=6, pady=4)

        welcome_title = ctk.CTkLabel(
            welcome_box,
            text="👋 Startup Welcome Greeting",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        welcome_title.pack(anchor="w", padx=10, pady=(6, 2))

        welcome_opts = ["English (Iron Man)", "Tamil (தமிழ்)", "Both (Dual Language)", "Custom Free Text", "Disabled (Silent)"]
        self.welcome_selector = ctk.CTkOptionMenu(
            welcome_box,
            values=welcome_opts,
            command=self._on_welcome_greeting_changed,
            height=28,
            corner_radius=4,
            fg_color="#111c2b",
            button_color="#1a2f47",
            button_hover_color="#234266",
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        if self.welcome_language == "custom":
            cur_wel = "Custom Free Text"
        elif self.welcome_language == "tamil":
            cur_wel = "Tamil (தமிழ்)"
        elif self.welcome_language == "both":
            cur_wel = "Both (Dual Language)"
        elif self.welcome_language == "disabled":
            cur_wel = "Disabled (Silent)"
        else:
            cur_wel = "English (Iron Man)"
        self.welcome_selector.set(cur_wel)
        self.welcome_selector.pack(fill="x", padx=10, pady=(0, 6))

        custom_lbl = ctk.CTkLabel(
            welcome_box,
            text="✍ Custom Welcome Message (Free Text):",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#a0c4df"
        )
        custom_lbl.pack(anchor="w", padx=10, pady=(2, 0))

        self.custom_welcome_entry = ctk.CTkEntry(
            welcome_box,
            placeholder_text="e.g. Welcome Tony, systems are standing by!",
            height=28,
            corner_radius=4,
            fg_color="#06121d",
            border_color="#103a54",
            border_width=1,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        if self.custom_welcome_message:
            self.custom_welcome_entry.insert(0, self.custom_welcome_message)
        self.custom_welcome_entry.pack(fill="x", padx=10, pady=(2, 6))

        custom_btn_row = ctk.CTkFrame(welcome_box, fg_color="transparent")
        custom_btn_row.pack(fill="x", padx=10, pady=(0, 8))

        test_custom_btn = ctk.CTkButton(
            custom_btn_row,
            text="🔊 Test Custom",
            width=85,
            height=26,
            corner_radius=4,
            fg_color="#11293a",
            hover_color="#1b3f59",
            border_color=self.COLOR_CYAN,
            border_width=1,
            text_color=self.COLOR_CYAN,
            font=ctk.CTkFont(family="Consolas", size=9),
            command=self._test_custom_welcome_message
        )
        test_custom_btn.pack(side="left")

        save_custom_btn = ctk.CTkButton(
            custom_btn_row,
            text="💾 Save Custom Msg",
            height=26,
            corner_radius=4,
            fg_color="#072b21",
            hover_color="#0e4737",
            border_color="#00ff88",
            border_width=1,
            text_color="#00ff88",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            command=self._save_custom_welcome_message
        )
        save_custom_btn.pack(side="right")

        # 3. Voice Speech Feedback Switch
        voice_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        voice_box.pack(fill="x", padx=6, pady=4)

        voice_label = ctk.CTkLabel(
            voice_box,
            text="🔊 Voice Speech Feedback",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffffff"
        )
        voice_label.pack(side="left", padx=10, pady=8)

        self.voice_switch = ctk.CTkSwitch(
            voice_box,
            text="ON" if self.voice_enabled else "OFF",
            command=self._on_voice_toggle,
            progress_color=self.COLOR_CYAN,
            button_color="#ffffff",
            button_hover_color="#e0f7fa"
        )
        if self.voice_enabled:
            self.voice_switch.select()
        else:
            self.voice_switch.deselect()
        self.voice_switch.pack(side="right", padx=10)

        # 4. Auto Tamil / Tanglish Voice Switch
        tamil_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#ff007f")
        tamil_box.pack(fill="x", padx=6, pady=4)

        tamil_label = ctk.CTkLabel(
            tamil_box,
            text="🇮🇳 Auto Tamil/Tanglish Voice",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ff77b4"
        )
        tamil_label.pack(side="left", padx=10, pady=8)

        self.tamil_switch = ctk.CTkSwitch(
            tamil_box,
            text="AUTO" if self.tamil_auto_switch else "OFF",
            command=self._on_tamil_toggle,
            progress_color=self.COLOR_MAGENTA,
            button_color="#ffffff",
            button_hover_color="#ffd1e6"
        )
        if self.tamil_auto_switch:
            self.tamil_switch.select()
        else:
            self.tamil_switch.deselect()
        self.tamil_switch.pack(side="right", padx=10)

        # 5. English Voice Persona (Iron Man Suite)
        char_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        char_box.pack(fill="x", padx=6, pady=4)

        char_label = ctk.CTkLabel(
            char_box,
            text="🎙 English Persona (Iron Man Suite)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffffff"
        )
        char_label.pack(anchor="w", padx=10, pady=(6, 2))

        english_options = list(self.english_voices.keys())
        self.voice_selector = ctk.CTkOptionMenu(
            char_box,
            values=english_options,
            command=self._on_english_persona_selected,
            height=28,
            corner_radius=4,
            fg_color="#111c2b",
            button_color="#1a2f47",
            button_hover_color="#234266",
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.voice_selector.set(self.selected_english_persona)
        self.voice_selector.pack(fill="x", padx=10, pady=(0, 8))

        # 6. Tamil Neural Voice Persona
        tamil_voice_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        tamil_voice_box.pack(fill="x", padx=6, pady=4)

        tamil_voice_label = ctk.CTkLabel(
            tamil_voice_box,
            text="🎙 Tamil Neural Voice Persona",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffffff"
        )
        tamil_voice_label.pack(anchor="w", padx=10, pady=(6, 2))

        tamil_options = list(self.tamil_voices.keys())
        self.tamil_voice_selector = ctk.CTkOptionMenu(
            tamil_voice_box,
            values=tamil_options,
            command=self._on_tamil_persona_selected,
            height=28,
            corner_radius=4,
            fg_color="#111c2b",
            button_color="#1a2f47",
            button_hover_color="#234266",
            text_color="#ff77b4",
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.tamil_voice_selector.set(self.selected_tamil_persona)
        self.tamil_voice_selector.pack(fill="x", padx=10, pady=(0, 8))

        # 7. Speech Velocity Slider
        speed_box = ctk.CTkFrame(self.tab_audio_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        speed_box.pack(fill="x", padx=6, pady=4)

        self.speed_label = ctk.CTkLabel(
            speed_box,
            text=f"⚡ Speech Velocity: {self.voice_rate} WPM",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffffff"
        )
        self.speed_label.pack(anchor="w", padx=10, pady=(6, 2))

        self.speed_slider = ctk.CTkSlider(
            speed_box,
            from_=130,
            to=240,
            number_of_steps=11,
            command=self._on_speed_changed,
            progress_color=self.COLOR_MAGENTA,
            button_color=self.COLOR_MAGENTA
        )
        self.speed_slider.set(self.voice_rate)
        self.speed_slider.pack(fill="x", padx=10, pady=(0, 8))

        # 8. Audio Diagnostic Tests
        test_audio_btn = ctk.CTkButton(
            self.tab_audio_frame,
            text="🔊 Test English Persona (JARVIS/FRIDAY)",
            height=30,
            corner_radius=4,
            fg_color="#11293a",
            hover_color="#1b3f59",
            border_color=self.COLOR_CYAN,
            border_width=1,
            text_color=self.COLOR_CYAN,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self._run_voice_test
        )
        test_audio_btn.pack(fill="x", padx=6, pady=(6, 3))

        test_tamil_btn = ctk.CTkButton(
            self.tab_audio_frame,
            text="🔊 Test Tamil Neural Speech",
            height=30,
            corner_radius=4,
            fg_color="#2b0a1a",
            hover_color="#45112a",
            border_color=self.COLOR_MAGENTA,
            border_width=1,
            text_color="#ff77b4",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self._run_tamil_test
        )
        test_tamil_btn.pack(fill="x", padx=6, pady=(3, 10))

        # ======================================================================
        # TAB 2: AI & VISION CONTROL
        # ======================================================================
        self.tab_ai_frame = ctk.CTkScrollableFrame(
            self.settings_frame,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.tab_ai_frame._create_grid = lambda: _hide_frame_scrollbar(self.tab_ai_frame)
        _hide_frame_scrollbar(self.tab_ai_frame)

        # Non-Vision Efficiency Priority Banner
        eff_box = ctk.CTkFrame(self.tab_ai_frame, fg_color="#071926", corner_radius=4, border_width=1, border_color="#00ff88")
        eff_box.pack(fill="x", padx=6, pady=4)

        eff_title = ctk.CTkLabel(
            eff_box,
            text="🛡 NON-VISION FIRST POLICY: ACTIVE",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#00ff88"
        )
        eff_title.pack(anchor="w", padx=10, pady=(6, 2))

        eff_desc = ctk.CTkLabel(
            eff_box,
            text="Direct tools (open app, launch URLs, run powershell, query apps) are strictly prioritized before invoking vision models to maximize speed and preserve Groq Free Tier TPM/RPM tokens.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#b6e7ff",
            justify="left",
            wraplength=290
        )
        eff_desc.pack(anchor="w", padx=10, pady=(0, 8))

        # Vision Autonomous Control (Token Saver) Switch
        vision_box = ctk.CTkFrame(self.tab_ai_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#ffe600")
        vision_box.pack(fill="x", padx=6, pady=4)

        vision_title_row = ctk.CTkFrame(vision_box, fg_color="transparent")
        vision_title_row.pack(fill="x", padx=10, pady=(8, 2))

        vision_title = ctk.CTkLabel(
            vision_title_row,
            text="👁 Vision Control (Token Saver)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffe600"
        )
        vision_title.pack(side="left")

        self.vision_switch = ctk.CTkSwitch(
            vision_title_row,
            text="ON" if self.is_vision_enabled else "OFF",
            command=self._on_vision_switch_toggle,
            progress_color="#00ff88",
            button_color="#ffffff",
            button_hover_color="#e0f7fa"
        )
        if self.is_vision_enabled:
            self.vision_switch.select()
        else:
            self.vision_switch.deselect()
        self.vision_switch.pack(side="right")

        vision_model_lbl = ctk.CTkLabel(
            vision_box,
            text="Perception Model (Visual Grounding):",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#a0c4df"
        )
        vision_model_lbl.pack(anchor="w", padx=10, pady=(4, 1))

        self.vision_model_selector = ctk.CTkOptionMenu(
            vision_box,
            values=VISION_MODELS,
            command=self._on_vision_model_selected,
            height=28,
            corner_radius=4,
            fg_color="#1a1805",
            button_color="#363008",
            button_hover_color="#544c10",
            text_color="#ffe600",
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.vision_model_selector.set(self.selected_vision_model)
        self.vision_model_selector.pack(fill="x", padx=10, pady=(2, 6))

        # Neural Core LLM Model Selection
        model_box = ctk.CTkFrame(self.tab_ai_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        model_box.pack(fill="x", padx=6, pady=4)

        model_title = ctk.CTkLabel(
            model_box,
            text="🧠 Neural Core LLM Engine",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#ffffff"
        )
        model_title.pack(anchor="w", padx=10, pady=(6, 2))

        self.settings_model_dropdown = ctk.CTkOptionMenu(
            model_box,
            values=self.available_models,
            command=self._on_model_selected,
            height=28,
            corner_radius=4,
            fg_color="#111c2b",
            button_color="#1a2f47",
            button_hover_color="#234266",
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.settings_model_dropdown.set(self.model_name)
        self.settings_model_dropdown.pack(fill="x", padx=10, pady=(2, 8))

        # Anti-Hang & Rate Guardrails Card
        safety_box = ctk.CTkFrame(self.tab_ai_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        safety_box.pack(fill="x", padx=6, pady=4)

        safety_title = ctk.CTkLabel(
            safety_box,
            text="⚙ Anti-Hang & Rate Guardrails",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        safety_title.pack(anchor="w", padx=10, pady=(6, 2))

        vision_info = ctk.CTkLabel(
            safety_box,
            text="• 429 Shield: Exp Backoff with Jitter\n• Step Throttle: 3.5s mandatory delay\n• Image Compression: 1280px • 75% JPEG\n• Safety: Failsafe Corner Abort\n• Bound: Max 10 autonomous steps",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#a0c4df",
            justify="left"
        )
        vision_info.pack(anchor="w", padx=10, pady=(0, 8))

        # ======================================================================
        # TAB 3: API KEYS & GATEWAYS
        # ======================================================================
        self.tab_api_frame = ctk.CTkScrollableFrame(
            self.settings_frame,
            fg_color="transparent",
            corner_radius=0,
            border_width=0
        )
        self.tab_api_frame._create_grid = lambda: _hide_frame_scrollbar(self.tab_api_frame)
        _hide_frame_scrollbar(self.tab_api_frame)

        # Groq API Key Box
        groq_key_box = ctk.CTkFrame(self.tab_api_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#00f0ff")
        groq_key_box.pack(fill="x", padx=6, pady=4)

        groq_title_row = ctk.CTkFrame(groq_key_box, fg_color="transparent")
        groq_title_row.pack(fill="x", padx=10, pady=(8, 2))

        groq_key_title = ctk.CTkLabel(
            groq_title_row,
            text="🔑 Groq API Key",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        groq_key_title.pack(side="left")

        self.groq_key_status = ctk.CTkLabel(
            groq_title_row,
            text="[CONFIGURED]" if self.current_api_key else "[MISSING]",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#00ff88" if self.current_api_key else "#ff4444"
        )
        self.groq_key_status.pack(side="right")

        self.groq_key_entry = ctk.CTkEntry(
            groq_key_box,
            placeholder_text="Enter gsk_... API Key",
            height=28,
            corner_radius=4,
            fg_color="#06121d",
            border_color="#103a54",
            border_width=1,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=10),
            show="•"
        )
        if self.current_api_key:
            self.groq_key_entry.insert(0, self.current_api_key)
        self.groq_key_entry.pack(fill="x", padx=10, pady=(4, 6))

        groq_btn_row = ctk.CTkFrame(groq_key_box, fg_color="transparent")
        groq_btn_row.pack(fill="x", padx=10, pady=(0, 8))

        self.show_groq_btn = ctk.CTkButton(
            groq_btn_row,
            text="👁 Show",
            width=65,
            height=26,
            corner_radius=4,
            fg_color="#0d1f30",
            hover_color="#193856",
            border_color="#00f0ff",
            border_width=1,
            text_color="#00f0ff",
            font=ctk.CTkFont(family="Consolas", size=9),
            command=self._toggle_show_groq_key
        )
        self.show_groq_btn.pack(side="left")

        save_groq_btn = ctk.CTkButton(
            groq_btn_row,
            text="💾 Save Groq Key",
            height=26,
            corner_radius=4,
            fg_color="#072b21",
            hover_color="#0e4737",
            border_color="#00ff88",
            border_width=1,
            text_color="#00ff88",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            command=self._save_groq_key
        )
        save_groq_btn.pack(side="right")

        # Telegram Bot API Configuration Box
        tg_config_box = ctk.CTkFrame(self.tab_api_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#00f0ff")
        tg_config_box.pack(fill="x", padx=6, pady=4)

        tg_title_row = ctk.CTkFrame(tg_config_box, fg_color="transparent")
        tg_title_row.pack(fill="x", padx=10, pady=(8, 2))

        tg_config_title = ctk.CTkLabel(
            tg_title_row,
            text="🤖 Telegram Bot Gateway",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        tg_config_title.pack(side="left")

        self.tg_status_label = ctk.CTkLabel(
            tg_title_row,
            text="[ACTIVE]" if self.telegram_token else "[INACTIVE]",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#00ff88" if self.telegram_token else "#ff4444"
        )
        self.tg_status_label.pack(side="right")

        tg_token_lbl = ctk.CTkLabel(
            tg_config_box,
            text="Bot Token (from @BotFather):",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#a0c4df"
        )
        tg_token_lbl.pack(anchor="w", padx=10, pady=(2, 0))

        self.tg_token_entry = ctk.CTkEntry(
            tg_config_box,
            placeholder_text="e.g. 9049041950:AAGCD0KcHkBy...",
            height=28,
            corner_radius=4,
            fg_color="#06121d",
            border_color="#103a54",
            border_width=1,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        if self.telegram_token:
            self.tg_token_entry.insert(0, self.telegram_token)
        self.tg_token_entry.pack(fill="x", padx=10, pady=(2, 4))

        tg_pass_lbl = ctk.CTkLabel(
            tg_config_box,
            text="Security Passcode (Default: 1234):",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#a0c4df"
        )
        tg_pass_lbl.pack(anchor="w", padx=10, pady=(2, 0))

        self.tg_pass_entry = ctk.CTkEntry(
            tg_config_box,
            placeholder_text="1234",
            height=28,
            corner_radius=4,
            fg_color="#06121d",
            border_color="#103a54",
            border_width=1,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.tg_pass_entry.insert(0, self.telegram_password)
        self.tg_pass_entry.pack(fill="x", padx=10, pady=(2, 6))

        save_tg_btn = ctk.CTkButton(
            tg_config_box,
            text="💾 Save Telegram API Config",
            height=26,
            corner_radius=4,
            fg_color="#072b21",
            hover_color="#0e4737",
            border_color="#00ff88",
            border_width=1,
            text_color="#00ff88",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            command=self._save_telegram_config
        )
        save_tg_btn.pack(fill="x", padx=10, pady=(4, 8))

        # Telegram Remote Directives Guide Card
        tg_guide_box = ctk.CTkFrame(self.tab_api_frame, fg_color="#0a0e17", corner_radius=4, border_width=1, border_color="#19283d")
        tg_guide_box.pack(fill="x", padx=6, pady=4)

        tg_guide_title = ctk.CTkLabel(
            tg_guide_box,
            text="📱 Remote Directives Guide",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#00f0ff"
        )
        tg_guide_title.pack(anchor="w", padx=10, pady=(6, 2))

        tg_guide_content = ctk.CTkLabel(
            tg_guide_box,
            text="• Send '1234' on initial contact to authenticate\n• 'send screenshot': Screen capture sent to chat\n• '/vision on' or '/vision off': Toggle vision\n• 'Open Chrome' / 'Close Notepad': App control\n• '/lock': Terminate authorized session",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#a0c4df",
            justify="left"
        )
        tg_guide_content.pack(anchor="w", padx=10, pady=(0, 8))

        # Initialize Default Tab View
        self._switch_settings_tab(self.active_settings_tab)

    def _switch_settings_tab(self, tab_name: str):
        """Switches between Audio, Vision, and API Link settings tabs."""
        self.active_settings_tab = tab_name

        # Hide all tab frames
        if hasattr(self, "tab_audio_frame"):
            self.tab_audio_frame.pack_forget()
        if hasattr(self, "tab_ai_frame"):
            self.tab_ai_frame.pack_forget()
        if hasattr(self, "tab_api_frame"):
            self.tab_api_frame.pack_forget()

        # Inactive style constants
        inact_fg = "#0a1017"
        inact_border = "#182838"
        inact_text = "#6485a3"

        # Active style constants
        act_fg = "#0d273d"
        act_border = "#00f0ff"
        act_text = "#00f0ff"

        # Reset button styles
        for btn in [self.tab_btn_audio, self.tab_btn_ai, self.tab_btn_api]:
            btn.configure(fg_color=inact_fg, border_color=inact_border, text_color=inact_text, border_width=1)

        # Activate selected tab
        if tab_name == "ai":
            self.tab_btn_ai.configure(fg_color=act_fg, border_color=act_border, text_color=act_text)
            self.tab_ai_frame.pack(fill="both", expand=True, padx=4, pady=2)
        elif tab_name == "api":
            self.tab_btn_api.configure(fg_color=act_fg, border_color=act_border, text_color=act_text)
            self.tab_api_frame.pack(fill="both", expand=True, padx=4, pady=2)
        else: # "audio"
            self.tab_btn_audio.configure(fg_color=act_fg, border_color=act_border, text_color=act_text)
            self.tab_audio_frame.pack(fill="both", expand=True, padx=4, pady=2)

    def _on_default_voice_changed(self, choice: str):
        if "tamil" in choice.lower():
            self.default_voice_language = "tamil"
        else:
            self.default_voice_language = "english"
        save_env_variable("DEFAULT_VOICE_LANGUAGE", self.default_voice_language)
        notice = f"🎙 [AUDIO CONFIG] Default voice engine set to: {choice}"
        self._add_system_notice(notice)
        logger.info(notice)

    def _on_welcome_greeting_changed(self, choice: str):
        choice_l = choice.lower()
        if "custom" in choice_l:
            self.welcome_language = "custom"
        elif "tamil" in choice_l:
            self.welcome_language = "tamil"
        elif "both" in choice_l:
            self.welcome_language = "both"
        elif "disabled" in choice_l or "silent" in choice_l:
            self.welcome_language = "disabled"
        else:
            self.welcome_language = "english"
        save_env_variable("WELCOME_LANGUAGE", self.welcome_language)
        notice = f"👋 [AUDIO CONFIG] Startup welcome greeting set to: {choice}"
        self._add_system_notice(notice)
        logger.info(notice)

    def _save_custom_welcome_message(self):
        msg = self.custom_welcome_entry.get().strip()
        self.custom_welcome_message = msg
        save_env_variable("CUSTOM_WELCOME_MESSAGE", msg)
        if msg:
            self.welcome_language = "custom"
            save_env_variable("WELCOME_LANGUAGE", "custom")
            if hasattr(self, "welcome_selector"):
                self.welcome_selector.set("Custom Free Text")
            notice = f"💾 [AUDIO CONFIG] Custom welcome message saved: '{msg[:40]}...'"
        else:
            notice = "⚠️ [AUDIO CONFIG] Custom welcome message cleared."
        self._add_system_notice(notice)
        logger.info(notice)

    def _test_custom_welcome_message(self):
        msg = self.custom_welcome_entry.get().strip() or getattr(self, "custom_welcome_message", "").strip()
        if not msg:
            self._add_system_notice("⚠️ [AUDIO CONFIG] Please enter a custom welcome message first.")
            return
        voice_to_use = self.tamil_voice_name if (self.default_voice_language == "tamil" or is_tamil_or_tanglish(msg)) else self.english_voice_name
        threading.Thread(
            target=self._speak_edge_tts,
            args=(msg, voice_to_use),
            daemon=True
        ).start()

    def _toggle_settings_view(self):
        """Toggles between main chat feed and cyberpunk settings view."""
        if self.is_settings_open:
            self.settings_frame.pack_forget()
            self.chat_frame.pack(fill="both", expand=True, padx=4, pady=2)
            self.bottom_frame.pack(fill="x", padx=10, pady=(4, 10))
            self.settings_btn.configure(text="⚙")
            self.is_settings_open = False
        else:
            self.chat_frame.pack_forget()
            self.bottom_frame.pack_forget()
            self.settings_frame.pack(fill="both", expand=True, padx=10, pady=4)
            self.settings_btn.configure(text="✕")
            self.is_settings_open = True

    def _toggle_show_groq_key(self):
        current = self.groq_key_entry.cget("show")
        if current == "•":
            self.groq_key_entry.configure(show="")
            self.show_groq_btn.configure(text="🔒 Hide")
        else:
            self.groq_key_entry.configure(show="•")
            self.show_groq_btn.configure(text="👁 Show")

    def _save_groq_key(self):
        new_key = self.groq_key_entry.get().strip()
        if not new_key:
            self._add_system_notice("⚠️ [CONFIG] Groq API Key cannot be empty.")
            return

        self.current_api_key = new_key
        save_env_variable("GROQ_API_KEY", new_key)
        self.groq_key_status.configure(text="[CONFIGURED]", text_color="#00ff88")
        self._add_system_notice("🔑 [CONFIG] Groq API Key updated and persisted to .env.")
        threading.Thread(target=self._discover_models, daemon=True).start()

    def _save_telegram_config(self):
        new_token = self.tg_token_entry.get().strip()
        new_pass = self.tg_pass_entry.get().strip() or "1234"

        self.telegram_token = new_token
        self.telegram_password = new_pass
        save_env_variable("TELEGRAM_BOT_TOKEN", new_token)
        save_env_variable("TELEGRAM_BOT_PASSWORD", new_pass)

        if new_token:
            self.tg_status_label.configure(text="[ACTIVE]", text_color="#00ff88")
            if not getattr(self, "telegram_running", False):
                self.telegram_running = True
                threading.Thread(target=self._telegram_polling_loop, daemon=True).start()
            self._add_system_notice("🤖 [CONFIG] Telegram API configuration updated and persisted to .env.")
        else:
            self.tg_status_label.configure(text="[INACTIVE]", text_color="#ff4444")
            self._add_system_notice("⚠️ [CONFIG] Telegram Bot Token cleared.")

    def _update_vision_toggle_ui(self):
        """Updates both the main GUI HUD button and settings switch to reflect is_vision_enabled."""
        is_on = getattr(self, "is_vision_enabled", False)
        if hasattr(self, "vision_btn") and self.vision_btn:
            if is_on:
                self.vision_btn.configure(
                    text="[VISION: ON]",
                    fg_color="#071926",
                    hover_color="#0c2e47",
                    border_color="#00f0ff",
                    text_color="#00ff88"
                )
            else:
                self.vision_btn.configure(
                    text="[VISION: OFF]",
                    fg_color="#181216",
                    hover_color="#2b141b",
                    border_color="#555555",
                    text_color="#ff4444"
                )

        if hasattr(self, "vision_switch") and self.vision_switch:
            if is_on:
                self.vision_switch.select()
                self.vision_switch.configure(text="ON")
            else:
                self.vision_switch.deselect()
                self.vision_switch.configure(text="OFF")

    def _toggle_vision_manual(self):
        """Manual user toggle for Vision Control from desktop GUI button."""
        new_state = not getattr(self, "is_vision_enabled", False)
        self.is_vision_enabled = new_state
        self._update_vision_toggle_ui()
        state_str = "ENABLED" if self.is_vision_enabled else "DISABLED"
        notice = f"👁 [VISION CONTROL] Vision perception mode {state_str} (Tokens {'conserved' if not self.is_vision_enabled else 'active'})."
        self._add_system_notice(notice)
        logger.info(notice)

    def _on_vision_switch_toggle(self):
        """Handler for Vision toggle switch inside Settings View."""
        new_state = bool(self.vision_switch.get())
        self.is_vision_enabled = new_state
        self._update_vision_toggle_ui()
        state_str = "ENABLED" if self.is_vision_enabled else "DISABLED"
        notice = f"👁 [VISION CONTROL] Settings: Vision mode {state_str}."
        self._add_system_notice(notice)
        logger.info(notice)

    def set_vision_state(self, enabled: bool, reason: str = "") -> Dict[str, Any]:
        """Enables or disables visual perception mode. 
        Use only when visual reasoning/clicking is strictly required, 
        and turn it back OFF immediately once visual steps are completed."""
        self.is_vision_enabled = bool(enabled)
        self.after(0, self._update_vision_toggle_ui)
        state_str = "ENABLED" if self.is_vision_enabled else "DISABLED"
        reason_str = f" • Reason: {reason}" if reason else ""
        notice = f"👁 [VISION CONTROL] AI Self-Toggle: Vision {state_str}{reason_str}"
        self.after(0, lambda: self._add_system_notice(notice))
        logger.info(notice)
        return {
            "status": "success",
            "is_vision_enabled": self.is_vision_enabled,
            "message": f"Vision perception mode {state_str}.{reason_str}"
        }

    def _on_voice_toggle(self):
        self.voice_enabled = bool(self.voice_switch.get())
        self.voice_switch.configure(text="ON" if self.voice_enabled else "OFF")
        logger.info(f"Voice Feedback toggled to: {self.voice_enabled}")

    def _on_tamil_toggle(self):
        self.tamil_auto_switch = bool(self.tamil_switch.get())
        self.tamil_switch.configure(text="AUTO" if self.tamil_auto_switch else "OFF")
        logger.info(f"Tamil/Tanglish auto-switch toggled to: {self.tamil_auto_switch}")

    def _on_tamil_persona_selected(self, choice: str):
        if choice in self.tamil_voices:
            self.selected_tamil_persona = choice
            self.tamil_voice_name = self.tamil_voices[choice]
            logger.info(f"Selected Tamil voice: {choice} -> {self.tamil_voice_name}")

    def _on_english_persona_selected(self, choice: str):
        if choice in self.english_voices:
            self.selected_english_persona = choice
            self.english_voice_name = self.english_voices[choice]
            logger.info(f"Selected English persona: {choice} -> {self.english_voice_name}")

    def _on_speed_changed(self, val):
        self.voice_rate = int(val)
        self.speed_label.configure(text=f"⚡ Speech Velocity: {self.voice_rate} WPM")

    def _run_voice_test(self):
        """Speaks an authentic Iron Man confirmation line."""
        is_friday = "FRIDAY" in self.selected_english_persona.upper()
        test_line = (
            "Welcome to the work, sir. The systems are ready to work."
            if is_friday
            else "Welcome to the work, sir. The systems are ready to work."
        )
        threading.Thread(
            target=self._speak_text_thread,
            args=(test_line,),
            daemon=True
        ).start()

    def _run_tamil_test(self):
        """Speaks a Tamil neural speech sample."""
        test_line = "வணக்கம்! உங்கள் கட்டளைக்கு காத்திருக்கிறேன். அனைத்து அமைப்புகளும் தயாராக உள்ளன."
        threading.Thread(
            target=self._speak_text_thread,
            args=(test_line,),
            daemon=True
        ).start()

    def _on_vision_model_selected(self, chosen: str):
        self.selected_vision_model = chosen
        logger.info(f"Vision model switched to: {chosen}")

    # --------------------------------------------------------------------------
    # CHAT BUBBLE RENDERING
    # --------------------------------------------------------------------------

    def _get_timestamp(self) -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    def _get_responsive_wrap(self, padding: int = 85, max_w: int = 680, min_w: int = 265) -> int:
        """Dynamically calculates text wrapping length so chat bubbles look stunning on both mobile and widescreen sizes."""
        try:
            w = self.winfo_width()
            return min(max_w, max(min_w, w - padding))
        except Exception:
            return min_w

    def _scroll_to_bottom(self):
        try:
            self.update_idletasks()
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
            self._sync_fixed_background()
        except Exception:
            pass

    def _add_user_message(self, text: str, source: str = "operator", timestamp: Optional[str] = None):
        """Renders user message bubble with frosted glassmorphism, hot magenta / cyan neon glass border, and specular highlight."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=2, pady=5)

        is_tg = (source == "telegram")
        border_col = "#00f0ff" if is_tg else "#ff007f"
        bg_col = "#071b2d" if is_tg else "#1d0822"
        specular_col = "#103c5c" if is_tg else "#4f1446"
        badge_bg = "#0b2842" if is_tg else "#350e3a"
        badge_text_col = "#70d6ff" if is_tg else "#ff77b4"
        time_str = timestamp if timestamp else self._get_timestamp()
        badge_title = "[TELEGRAM]" if is_tg else "[OPERATOR]"
        wrap_width = self._get_responsive_wrap(padding=85)

        # Frosted glass card
        bubble = ctk.CTkFrame(
            container,
            fg_color=bg_col,
            corner_radius=4,
            border_width=1,
            border_color=border_col
        )
        bubble.pack(anchor="e", padx=(25, 4))

        # Specular light reflection strip along top edge of glass
        specular = ctk.CTkFrame(bubble, fg_color=specular_col, height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        # Header Row with Frosted Pill Badge
        header_row = ctk.CTkFrame(bubble, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(5, 3))

        badge = ctk.CTkFrame(header_row, fg_color=badge_bg, corner_radius=2)
        badge.pack(side="left")
        badge_lbl = ctk.CTkLabel(
            badge,
            text=f" {badge_title} ",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color=badge_text_col
        )
        badge_lbl.pack(padx=5, pady=2)

        time_lbl = ctk.CTkLabel(
            header_row,
            text=f"• {time_str}",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#c896bd" if not is_tg else "#6ba0be"
        )
        time_lbl.pack(side="left", padx=(6, 0))

        # Frosted Dot Indicator
        dots = ctk.CTkLabel(
            header_row,
            text="● ● ●",
            font=ctk.CTkFont(size=8),
            text_color=border_col
        )
        dots.pack(side="right")

        # Clean display text if starts with prefix
        display_text = text
        if display_text.startswith("[TELEGRAM] "):
            display_text = display_text[len("[TELEGRAM] "):]

        content = ctk.CTkLabel(
            bubble,
            text=display_text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#ffffff",
            justify="left",
            wraplength=wrap_width
        )
        content.pack(anchor="w", padx=14, pady=(2, 10))

        self._scroll_to_bottom()

    def _add_system_notice(self, notice_text: str):
        """Renders a system status notice card in chat feed with frosted glassmorphism."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=4, pady=5)
        wrap_width = self._get_responsive_wrap(padding=70)

        bubble = ctk.CTkFrame(
            container,
            fg_color="#061b24",
            corner_radius=4,
            border_width=1,
            border_color="#00ff88"
        )
        bubble.pack(anchor="w", padx=(4, 25), fill="x")

        # Specular light reflection strip
        specular = ctk.CTkFrame(bubble, fg_color="#0e4539", height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        header_row = ctk.CTkFrame(bubble, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(4, 2))

        badge = ctk.CTkFrame(header_row, fg_color="#082b21", corner_radius=2)
        badge.pack(side="left")
        badge_lbl = ctk.CTkLabel(
            badge,
            text=f" [SYS.LINK] • {self._get_timestamp()} ",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#00ff88"
        )
        badge_lbl.pack(padx=4, pady=1)

        content = ctk.CTkLabel(
            bubble,
            text=notice_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#d0f4ff",
            justify="left",
            wraplength=wrap_width
        )
        content.pack(anchor="w", padx=12, pady=(2, 8))

        self._scroll_to_bottom()

    def _add_ai_message(self, text: str, timestamp: Optional[str] = None):
        """Renders AI message bubble with frosted glassmorphism, glowing ice cyan edge, specular highlight, and cyber pill badge."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=2, pady=5)

        is_friday = "FRIDAY" in getattr(self, "selected_english_persona", "").upper()
        persona_tag = "[FRIDAY 2.0]" if is_friday else "[JARVIS 2.0]"
        time_str = timestamp if timestamp else self._get_timestamp()
        wrap_width = self._get_responsive_wrap(padding=85)

        # Frosted glass card with 1px glowing cyan glass border
        bubble = ctk.CTkFrame(
            container,
            fg_color="#071728",
            corner_radius=4,
            border_width=1,
            border_color="#00f0ff"
        )
        bubble.pack(anchor="w", padx=(4, 25))

        # Specular light reflection strip along top edge of glass
        specular = ctk.CTkFrame(bubble, fg_color="#103c5c", height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        # Glass Header Row with Frosted Pill Badge
        header_row = ctk.CTkFrame(bubble, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(5, 3))

        badge = ctk.CTkFrame(header_row, fg_color="#0b2842", corner_radius=2)
        badge.pack(side="left")
        badge_lbl = ctk.CTkLabel(
            badge,
            text=f" {persona_tag} ",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#00f0ff"
        )
        badge_lbl.pack(padx=5, pady=2)

        time_lbl = ctk.CTkLabel(
            header_row,
            text=f"• {time_str}",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#6ba0be"
        )
        time_lbl.pack(side="left", padx=(6, 0))

        # Frosted Glass Watermark
        hex_watermark = ctk.CTkLabel(
            header_row,
            text="⬡⬡⬢",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=11, weight="bold"),
            text_color="#00d9ff"
        )
        hex_watermark.pack(side="right")

        content = ctk.CTkLabel(
            bubble,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#e2f5ff",
            justify="left",
            wraplength=wrap_width
        )
        content.pack(anchor="w", padx=14, pady=(2, 10))

        self._scroll_to_bottom()

    def _add_tool_event_card(self, func_name: str, args: Dict[str, Any], result: Dict[str, Any], timestamp: Optional[str] = None):
        """Renders tool call action card with frosted amber glassmorphism and specular highlight."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=2, pady=5)

        status = result.get("status", "info")
        icon = "⚡" if func_name == "open_application" else (
            "🛑" if func_name == "close_application" else (
                "🔍" if func_name == "list_running_applications" else (
                    "🩺" if func_name == "get_system_health" else (
                        "💻" if func_name == "execute_command" else (
                            "📸" if func_name == "take_screenshot" else (
                                "👁" if func_name in ["run_autonomous_gui_agent", "set_vision_state"] else "🌐"
                            )
                        )
                    )
                )
            )
        )
        status_tag = "[SUCCESS]" if status == "success" else ("[NOTICE]" if status == "not_running" else "[ERROR]")
        status_color = "#00ff88" if status == "success" else (
            "#ffe600" if status == "not_running" else "#ff4444"
        )
        wrap_width = self._get_responsive_wrap(padding=70)

        card = ctk.CTkFrame(
            container,
            fg_color="#181404",
            corner_radius=4,
            border_width=1,
            border_color="#ffe600"
        )
        card.pack(anchor="w", padx=(4, 6), fill="x")

        # Specular light reflection strip
        specular = ctk.CTkFrame(card, fg_color="#453a08", height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        if func_name == "execute_command":
            cmd = args.get("command", "")
            shell = args.get("shell_type", "powershell").upper()
            cmd_preview = cmd if len(cmd) <= 24 else cmd[:21] + "..."
            header_text = f"💻 {shell}: {cmd_preview}"
        elif func_name == "get_system_health":
            header_text = "🩺 EXEC: get_system_health()"
        elif func_name == "take_screenshot":
            header_text = "📸 EXEC: capture_screenshot()"
        elif func_name == "run_autonomous_gui_agent":
            goal_preview = args.get("goal", "")
            if len(goal_preview) > 22:
                goal_preview = goal_preview[:19] + "..."
            header_text = f"👁 AUTO-GUI: {goal_preview}"
        elif func_name == "set_vision_state":
            en_val = args.get("enabled", False)
            state_tag = "ON" if en_val else "OFF"
            header_text = f"👁 EXEC: set_vision_state({state_tag})"
        elif func_name == "list_running_applications":
            header_text = "🔍 EXEC: list_running_applications()"
        else:
            arg_val = args.get("app_name", args.get("url", ""))
            arg_str = f"'{arg_val}'" if arg_val else ""
            header_text = f"{icon} EXEC: {func_name}({arg_str})"

        # Header Row with Glass Pill Badge
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(4, 2))

        badge = ctk.CTkFrame(header_row, fg_color="#332a07", corner_radius=2)
        badge.pack(side="left")
        badge_lbl = ctk.CTkLabel(
            badge,
            text=f" {header_text} ",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#ffe600"
        )
        badge_lbl.pack(padx=5, pady=2)

        hex_watermark = ctk.CTkLabel(
            header_row,
            text="⬡⬢",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=11, weight="bold"),
            text_color="#ffe600"
        )
        hex_watermark.pack(side="right")

        outcome_text = f"{status_tag} {result.get('message', 'Completed')}"
        outcome = ctk.CTkLabel(
            card,
            text=outcome_text,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=status_color,
            justify="left",
            wraplength=wrap_width
        )
        outcome.pack(anchor="w", padx=12, pady=(2, 8))

        self._scroll_to_bottom()

    def _add_vision_step_card(self, step_num: int, max_steps: int, thought: str, action_str: str, thumb_path: Optional[str] = None):
        """Renders visual step card with frosted glassmorphism, thought, action details, and thumbnail."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=2, pady=5)
        wrap_width = self._get_responsive_wrap(padding=70)

        card = ctk.CTkFrame(
            container,
            fg_color="#071929",
            corner_radius=4,
            border_width=1,
            border_color="#00f0ff"
        )
        card.pack(anchor="w", padx=(4, 6), fill="x")

        # Specular light reflection strip
        specular = ctk.CTkFrame(card, fg_color="#103c5c", height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        # Header Row
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(4, 2))

        badge = ctk.CTkFrame(header_row, fg_color="#0b2842", corner_radius=2)
        badge.pack(side="left")
        lbl = ctk.CTkLabel(
            badge,
            text=f" 👁 AUTO-GUI • STEP {step_num}/{max_steps} ",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#00f0ff"
        )
        lbl.pack(padx=5, pady=2)

        ts = ctk.CTkLabel(
            header_row,
            text=self._get_timestamp(),
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#6ba0be"
        )
        ts.pack(side="right")

        # Action Summary
        act_lbl = ctk.CTkLabel(
            card,
            text=f"⚡ Action: {action_str}",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#ffe600",
            anchor="w"
        )
        act_lbl.pack(anchor="w", padx=12, pady=(2, 1))

        # Thought Process
        if thought:
            thought_lbl = ctk.CTkLabel(
                card,
                text=f"🧠 {thought}",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#bce7fd",
                justify="left",
                wraplength=wrap_width
            )
            thought_lbl.pack(anchor="w", padx=12, pady=(1, 4))

        # Thumbnail Image Attachment
        if thumb_path and os.path.exists(thumb_path):
            try:
                with Image.open(thumb_path) as pil_img:
                    img_copy = pil_img.copy()
                    img_copy.thumbnail((250, 140))
                    ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
                    img_lbl = ctk.CTkLabel(card, image=ctk_img, text="", cursor="hand2")
                    img_lbl.image = ctk_img
                    img_lbl.pack(anchor="center", padx=10, pady=(4, 8))
                    img_lbl.bind("<Button-1>", lambda e, p=thumb_path: os.startfile(p) if hasattr(os, "startfile") else None)
            except Exception as ex:
                logger.error(f"Thumbnail preview error: {ex}")

        self._scroll_to_bottom()

    def _add_error_bubble(self, error_message: str):
        """Renders error notification bubble in chat with frosted ruby glassmorphism."""
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", padx=4, pady=5)
        wrap_width = self._get_responsive_wrap(padding=70)

        bubble = ctk.CTkFrame(
            container,
            fg_color="#24080a",
            corner_radius=4,
            border_width=1,
            border_color="#ff4444"
        )
        bubble.pack(anchor="w", padx=(4, 25))

        specular = ctk.CTkFrame(bubble, fg_color="#541217", height=2, corner_radius=2)
        specular.pack(fill="x", padx=6, pady=(3, 1))

        header = ctk.CTkLabel(
            bubble,
            text=f"[SYS.ALERT] • {self._get_timestamp()}",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#fca5a5"
        )
        header.pack(anchor="w", padx=12, pady=(4, 2))

        content = ctk.CTkLabel(
            bubble,
            text=error_message,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#fee2e2",
            justify="left",
            wraplength=wrap_width
        )
        content.pack(anchor="w", padx=12, pady=(1, 8))

        self._scroll_to_bottom()

    def _show_welcome_message(self):
        """Displays the pixel-perfect cyber conversation timeline matching Image 1, and announces readiness."""
        now_hour = datetime.datetime.now().hour
        if now_hour < 12:
            time_greeting = "Good morning"
        elif now_hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        is_friday = "FRIDAY" in self.selected_english_persona.upper()
        title_call = "boss" if is_friday else "sir"

        # Image 1 Target Timeline Items (Exact Pixel-Match):
        # 1. Operator: "what is your name"
        self._add_user_message("what is your name", source="operator", timestamp="03:01 PM")

        # 2. JARVIS 2.0 introduction
        self._add_ai_message(
            "I'm **JARVIS 2.0** - your cyber-punk-styled Windows desktop assistant. Feel free to call me JARVIS!",
            timestamp="03:01 PM"
        )

        # 3. Operator: "list that now what process are running in my pc"
        self._add_user_message("list that now what process are running in my pc", source="operator", timestamp="03:02 PM")

        # 4. Tool Execution Card: list_running_applications
        self._add_tool_event_card(
            "list_running_applications",
            {},
            {
                "status": "success",
                "message": "Found 5 active application(s): Google Chrome, Microsoft Edge, Terminal / Command Prompt, PowerShell, File Explorer."
            }
        )

        # 5. JARVIS 2.0 response listing running applications
        self._add_ai_message(
            "**Running applications (5)**\n\n"
            "- Google Chrome\n"
            "- Microsoft Edge\n"
            "- Terminal / Command Prompt\n"
            "- PowerShell\n"
            "- File Explorer\n\n"
            "Let me know if you'd like to close any of them, open something new, or run a command!",
            timestamp="03:03 PM"
        )

        # Speak startup greeting based on configured welcome_language
        welcome_mode = getattr(self, "welcome_language", "english").lower()
        if self.voice_enabled and welcome_mode != "disabled":
            def _play_welcome():
                eng_greeting = f"{time_greeting}, {title_call}. All systems are initialized and ready for work."
                tamil_greeting = "வணக்கம்! அனைத்து அமைப்புகளும் துவக்கப்பட்டு வேலைக்கு தயாராக உள்ளன."
                custom_msg = getattr(self, "custom_welcome_message", "").strip()

                if welcome_mode == "custom" and custom_msg:
                    voice_to_use = self.tamil_voice_name if (self.default_voice_language == "tamil" or is_tamil_or_tanglish(custom_msg)) else self.english_voice_name
                    self._speak_edge_tts(custom_msg, voice_to_use)
                elif welcome_mode in ["english", "both"]:
                    self._speak_edge_tts(eng_greeting, self.english_voice_name)
                    if welcome_mode == "both":
                        time.sleep(0.5)
                if welcome_mode in ["tamil", "both"]:
                    self._speak_edge_tts(tamil_greeting, self.tamil_voice_name)

            threading.Thread(target=_play_welcome, daemon=True).start()

    # --------------------------------------------------------------------------
    # EVENT HANDLERS
    # --------------------------------------------------------------------------

    def _update_status(self, text: str, is_error: bool = False, is_active: bool = False):
        color = "#ff4444" if is_error else (self.COLOR_YELLOW if is_active else self.COLOR_GREEN)
        self.status_indicator.configure(text=text, text_color=color)

    def _set_inputs_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.msg_entry.configure(state=state)
        self.send_btn.configure(state=state)
        self.clear_btn.configure(state=state)
        if enabled:
            self.msg_entry.focus_set()

    def _quick_action(self, prompt: str):
        """Executes a quick HUD directive."""
        if self.is_processing:
            return
        self.msg_entry.delete(0, "end")
        self.msg_entry.insert(0, prompt)
        self._on_send_clicked()

    def _on_clear_clicked(self):
        if self.is_processing:
            return
        self.stop_speech()
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self._update_status("● [SYS.ONLINE]", is_error=False)
        self._show_welcome_message()
        self.after(60, self._draw_cyber_circuits)

    def _on_send_clicked(self):
        user_input = self.msg_entry.get().strip()
        if not user_input:
            return

        # Check for immediate abort directive
        if user_input.lower() in ["abort", "stop", "exit", "cancel"]:
            if self.is_vision_running:
                self.msg_entry.delete(0, "end")
                self._on_abort_clicked()
                return

        if self.is_processing or self.is_vision_running:
            return

        self.stop_speech()
        self.msg_entry.delete(0, "end")

        # Check for direct autonomous GUI prompt triggers (e.g. "auto: ...", "gui: ...", "vision: ...")
        for prefix in ["auto:", "gui:", "vision:"]:
            if user_input.lower().startswith(prefix):
                goal = user_input[len(prefix):].strip()
                if goal:
                    self._add_user_message(user_input)
                    self._start_autonomous_gui_agent(goal)
                    return

        api_key = self.current_api_key or os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            self._add_user_message(user_input)
            self._add_error_bubble(
                "Missing GROQ_API_KEY in .env file!\n"
                "Please configure GROQ_API_KEY in your .env file."
            )
            self._update_status("● [NO.KEY.DETECTED]", is_error=True)
            return

        self._add_user_message(user_input)

        self.is_processing = True
        self._set_inputs_enabled(False)
        self._update_status("● [NEURAL.COMPUTING...]", is_active=True)

        threading.Thread(
            target=self._process_message_thread,
            args=(user_input, api_key),
            daemon=True
        ).start()

    # --------------------------------------------------------------------------
    # GROQ API & TOOL EXECUTION THREAD
    # --------------------------------------------------------------------------

    def _process_message_thread(self, user_prompt: str, api_key: str):
        try:
            if Groq is None:
                raise RuntimeError("The 'groq' package is not installed. Run: pip install groq")

            client = Groq(api_key=api_key)
            self.conversation_history.append({"role": "user", "content": user_prompt})

            max_tool_rounds = 5
            current_round = 0
            final_spoken_text = ""

            while current_round < max_tool_rounds:
                current_round += 1

                self.after(0, lambda: self._update_status(f"● [THINKING: {self.model_name}]...", is_active=True))

                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=self.conversation_history,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=2048
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if not tool_calls:
                    content = response_message.content or "Command completed."
                    final_spoken_text = content
                    self.conversation_history.append({"role": "assistant", "content": content})
                    self.after(0, lambda c=content: self._add_ai_message(c))
                    break

                assistant_record = {
                    "role": "assistant",
                    "content": response_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in tool_calls
                    ]
                }
                self.conversation_history.append(assistant_record)

                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args_raw = tool_call.function.arguments or "{}"
                    try:
                        func_args = json.loads(func_args_raw)
                    except json.JSONDecodeError:
                        func_args = {"app_name": func_args_raw}

                    app_arg = func_args.get("app_name", func_args.get("url", ""))
                    status_text = f"● [RUNNING: {func_name}]..."
                    self.after(0, lambda st=status_text: self._update_status(st, is_active=True))

                    if func_name in AVAILABLE_TOOLS:
                        tool_func = AVAILABLE_TOOLS[func_name]
                        if func_name == "list_running_applications":
                            result = tool_func()
                        elif func_name == "get_system_health":
                            result = tool_func()
                        elif func_name == "open_website":
                            result = tool_func(func_args.get("url", ""))
                        elif func_name == "execute_command":
                            result = tool_func(
                                command=func_args.get("command", ""),
                                shell_type=func_args.get("shell_type", "powershell")
                            )
                        elif func_name == "take_screenshot":
                            result = tool_func(func_args.get("filename"))
                        elif func_name == "run_autonomous_gui_agent":
                            goal_arg = func_args.get("goal", "")
                            result = self._deploy_autonomous_gui_from_tool(goal_arg)
                        elif func_name == "set_vision_state":
                            result = self.set_vision_state(
                                enabled=func_args.get("enabled", False),
                                reason=func_args.get("reason", "")
                            )
                        else:
                            result = tool_func(func_args.get("app_name", ""))
                    else:
                        result = {"status": "error", "message": f"Tool '{func_name}' not recognized."}

                    self.after(0, lambda fn=func_name, fa=func_args, res=result: self._add_tool_event_card(fn, fa, res))

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": json.dumps(result)
                    })

            self.after(0, lambda: self._update_status("● [SYS.ONLINE]", is_error=False))

            # Trigger Text-to-Speech audio speech feedback
            if final_spoken_text and self.voice_enabled:
                threading.Thread(
                    target=self._speak_text_thread,
                    args=(final_spoken_text,),
                    daemon=True
                ).start()

        except NotFoundError as nf_err:
            logger.error(f"Model Not Found Error: {nf_err}")
            err_msg = f"Model `{self.model_name}` not accessible.\nSwitch model in settings."
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [MODEL.ERR]", is_error=True))
            self._discover_models()

        except AuthenticationError as auth_err:
            logger.error(f"Auth Error: {auth_err}")
            err_msg = f"Invalid API Key in .env file!\nDetails: {str(auth_err)}"
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [AUTH.ERR]", is_error=True))

        except RateLimitError:
            err_msg = "Rate limit exceeded. Please wait a moment."
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [RATE.LIMIT]", is_error=True))

        except APIConnectionError:
            err_msg = "Network connection failed. Check your internet."
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [NET.ERR]", is_error=True))

        except APIError as api_err:
            status_code = getattr(api_err, "status_code", "Error")
            err_msg = f"Groq API Error ({status_code}): {getattr(api_err, 'message', str(api_err))}"
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [API.ERR]", is_error=True))

        except Exception as ex:
            logger.exception("Worker error:")
            err_msg = f"Unexpected error: {str(ex)}"
            self.after(0, lambda: self._add_error_bubble(err_msg))
            self.after(0, lambda: self._update_status("● [FATAL.ERR]", is_error=True))

        finally:
            self.is_processing = False
            self.after(0, lambda: self._set_inputs_enabled(True))

    # --------------------------------------------------------------------------
    # TELEGRAM BOT INTEGRATION & REMOTE CONTROL
    # --------------------------------------------------------------------------

    def _telegram_polling_loop(self):
        """Continuously long-polls Telegram for incoming instructions and requests."""
        logger.info(f"Telegram polling loop active for token {self.telegram_token[:10]}...")
        while self.telegram_running:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_token}/getUpdates"
                params = {"offset": self.telegram_offset, "timeout": 15}
                res = requests.get(url, params=params, timeout=20)
                if res.status_code != 200:
                    time.sleep(2)
                    continue

                data = res.json()
                if not data.get("ok"):
                    time.sleep(2)
                    continue

                for update in data.get("result", []):
                    upd_id = update["update_id"]
                    self.telegram_offset = max(self.telegram_offset, upd_id + 1)

                    message = update.get("message") or update.get("edited_message")
                    if not message:
                        continue

                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    if not chat_id:
                        continue

                    text = (message.get("text") or "").strip()
                    from_user = message.get("from", {})
                    user_display = from_user.get("first_name") or from_user.get("username") or f"Operator_{chat_id}"

                    self._handle_telegram_message(chat_id, user_display, text)

            except requests.RequestException:
                time.sleep(2)
            except Exception as ex:
                logger.error(f"Telegram polling loop exception: {ex}")
                time.sleep(2)

    def _handle_telegram_message(self, chat_id: int, user_display: str, text: str):
        """Validates security passcode and routes commands to Groq AI or tools."""
        if not text:
            return

        # 1. Gatekeeper: Validate passcode if chat is not authenticated
        if chat_id not in self.telegram_authenticated_chats:
            if text == self.telegram_password:
                self.telegram_authenticated_chats.add(chat_id)
                welcome_reply = (
                    "⚡ ACCESS GRANTED • JARVIS 2.0 ONLINE\n\n"
                    f"Welcome, {user_display}! Passcode verified.\n"
                    "Your session is now authorized to command this Windows workstation.\n\n"
                    "Directives:\n"
                    "• 'Open Chrome' / 'Close Calculator'\n"
                    "• 'List all apps installed on my PC'\n"
                    "• 'Run powershell: Get-Process'\n"
                    "• 'What apps are open?'\n"
                    "• 'Send screenshot' to receive desktop screen capture\n"
                    "• Type '/lock' to terminate this session"
                )
                send_telegram_message(self.telegram_token, chat_id, welcome_reply)
                self.after(0, lambda: self._add_system_notice(
                    f"🤖 [TELEGRAM] Authorized remote session connected for {user_display} (Chat: {chat_id})."
                ))
                return
            else:
                # Challenge for password
                challenge = (
                    "🔒 ACCESS RESTRICTED • JARVIS 2.0 SECURITY GATEWAY\n\n"
                    "Authorization required to control this Windows workstation.\n"
                    "Please enter the security passcode to proceed:"
                )
                send_telegram_message(self.telegram_token, chat_id, challenge)
                self.after(0, lambda: self._add_system_notice(
                    f"⚠️ [TELEGRAM] Unauthorized access attempt from {user_display} (Chat: {chat_id}). Challenged for passcode."
                ))
                return

        # 2. Authenticated Session: Check for logout / lock directive
        if text.lower() in ["/lock", "lock", "/logout", "logout", "exit"]:
            self.telegram_authenticated_chats.discard(chat_id)
            send_telegram_message(self.telegram_token, chat_id, "🔒 Session locked. Enter passcode to reconnect.")
            self.after(0, lambda: self._add_system_notice(
                f"🔒 [TELEGRAM] Remote session locked by {user_display}."
            ))
            return

        # Check for emergency remote abort directive
        if text.lower() in ["/abort", "abort", "/stop", "stop"]:
            if self.is_vision_running:
                self.vision_abort_event.set()
                send_telegram_message(self.telegram_token, chat_id, "🛑 Emergency abort triggered. Stopping Autonomous GUI Agent.")
                self.after(0, lambda: self._add_system_notice(f"🛑 [TELEGRAM ABORT] Operator {user_display} aborted the autonomous GUI sequence."))
                return
            else:
                send_telegram_message(self.telegram_token, chat_id, "ℹ️ No autonomous GUI sequence is currently active.")
                return

        # Check for remote Vision Control directives
        clean_t = text.lower().strip()
        if clean_t in ["/vision on", "/vision enable", "vision on", "enable vision", "turn on vision"]:
            self.set_vision_state(True, reason=f"Remote Telegram command from {user_display}")
            send_telegram_message(self.telegram_token, chat_id, "👁 VISION CONTROL: ENABLED [ON]\nAutonomous visual perception mode is now active.")
            return
        elif clean_t in ["/vision off", "/vision disable", "vision off", "disable vision", "turn off vision"]:
            self.set_vision_state(False, reason=f"Remote Telegram command from {user_display}")
            send_telegram_message(self.telegram_token, chat_id, "👁 VISION CONTROL: DISABLED [OFF]\nVisual perception mode deactivated to conserve Groq tokens.")
            return
        elif clean_t in ["/vision", "vision status"]:
            state_str = "ENABLED [ON]" if self.is_vision_enabled else "DISABLED [OFF]"
            send_telegram_message(self.telegram_token, chat_id, f"👁 VISION CONTROL STATUS: {state_str}\nUse /vision on or /vision off to toggle.")
            return

        # Check for direct Autonomous GUI directives from Telegram (e.g. "auto: ...", "/auto ...")
        for prefix in ["auto:", "/auto ", "gui:", "vision:"]:
            if text.lower().startswith(prefix):
                goal = text[len(prefix):].strip()
                if goal:
                    self.after(0, lambda: self._add_user_message(text, source="telegram"))
                    self._start_autonomous_gui_agent(goal, source="telegram", chat_id=chat_id)
                    return

        # 3. Check for Direct Screenshot Request
        lower = text.lower().strip()
        screenshot_keywords = [
            "screenshot", "screen shot", "send screenshot", "send screen shot",
            "take screenshot", "take screen shot", "capture screen", "capture screenshot",
            "ss", "get screenshot", "send me screenshot", "send me a screenshot",
            "give screenshot", "screen snapshot"
        ]
        is_screenshot = (lower in screenshot_keywords) or ("screenshot" in lower or "screen shot" in lower)

        if is_screenshot:
            send_telegram_chat_action(self.telegram_token, chat_id, "upload_photo")
            self.after(0, lambda: self._add_user_message(text, source="telegram"))
            try:
                img_path = capture_screenshot()
                caption = f"⚡ JARVIS 2.0 • Desktop Screen Capture [{self._get_timestamp()}]"
                sent = send_telegram_photo(self.telegram_token, chat_id, img_path, caption=caption)
                if sent:
                    res_dict = {
                        "status": "success",
                        "file_path": img_path,
                        "message": "Desktop screenshot captured and dispatched to Telegram."
                    }
                    self.after(0, lambda: self._add_tool_event_card("take_screenshot", {"target": "Telegram"}, res_dict))
                    reply_msg = "Workstation screen captured and dispatched to your Telegram session, Operator."
                    self.after(0, lambda: self._add_ai_message(reply_msg))
                    if self.voice_enabled:
                        threading.Thread(target=self._speak_text_thread, args=(reply_msg,), daemon=True).start()
                else:
                    send_telegram_message(self.telegram_token, chat_id, "❌ Error: Failed to upload screenshot to Telegram.")
            except Exception as e:
                logger.error(f"Error executing screenshot for Telegram: {e}")
                send_telegram_message(self.telegram_token, chat_id, f"❌ Screenshot error: {str(e)}")
            return

        # 4. Standard AI Command Execution via Groq + Local Windows Tools
        self.after(0, lambda: self._add_user_message(text, source="telegram"))
        threading.Thread(
            target=self._execute_telegram_command,
            args=(text, chat_id, user_display),
            daemon=True
        ).start()

    def _execute_telegram_command(self, user_prompt: str, chat_id: int, user_display: str):
        """Processes Telegram instruction through Groq AI, executes local tools, and replies."""
        api_key = self.current_api_key
        if not api_key:
            send_telegram_message(
                self.telegram_token,
                chat_id,
                "⚠️ JARVIS 2.0: Missing GROQ_API_KEY on workstation. Please configure .env file."
            )
            return

        try:
            send_telegram_chat_action(self.telegram_token, chat_id, "typing")
            self.after(0, lambda: self._update_status(f"● [TELEGRAM: {user_display}]...", is_active=True))

            client = Groq(api_key=api_key)
            self.conversation_history.append({"role": "user", "content": f"[From Telegram Operator: {user_display}] {user_prompt}"})

            max_tool_rounds = 5
            current_round = 0
            final_spoken_text = ""
            captured_screenshots = []

            while current_round < max_tool_rounds:
                current_round += 1

                send_telegram_chat_action(self.telegram_token, chat_id, "typing")
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=self.conversation_history,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=2048
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if not tool_calls:
                    content = response_message.content or "Command executed."
                    final_spoken_text = content
                    self.conversation_history.append({"role": "assistant", "content": content})
                    self.after(0, lambda c=content: self._add_ai_message(c))
                    break

                assistant_record = {
                    "role": "assistant",
                    "content": response_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in tool_calls
                    ]
                }
                self.conversation_history.append(assistant_record)

                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args_raw = tool_call.function.arguments or "{}"
                    try:
                        func_args = json.loads(func_args_raw)
                    except json.JSONDecodeError:
                        func_args = {"app_name": func_args_raw}

                    send_telegram_chat_action(self.telegram_token, chat_id, "typing")
                    status_text = f"● [RUNNING: {func_name}]..."
                    self.after(0, lambda st=status_text: self._update_status(st, is_active=True))

                    if func_name in AVAILABLE_TOOLS:
                        tool_func = AVAILABLE_TOOLS[func_name]
                        if func_name == "list_running_applications":
                            result = tool_func()
                        elif func_name == "get_system_health":
                            result = tool_func()
                        elif func_name == "open_website":
                            result = tool_func(func_args.get("url", ""))
                        elif func_name == "execute_command":
                            result = tool_func(
                                command=func_args.get("command", ""),
                                shell_type=func_args.get("shell_type", "powershell")
                            )
                        elif func_name == "take_screenshot":
                            result = tool_func(func_args.get("filename"))
                            if result.get("status") == "success" and result.get("file_path"):
                                captured_screenshots.append(result["file_path"])
                        elif func_name == "run_autonomous_gui_agent":
                            goal_arg = func_args.get("goal", "")
                            result = self._deploy_autonomous_gui_from_tool(goal_arg, source="telegram", chat_id=chat_id)
                        elif func_name == "set_vision_state":
                            result = self.set_vision_state(
                                enabled=func_args.get("enabled", False),
                                reason=func_args.get("reason", "")
                            )
                        else:
                            result = tool_func(func_args.get("app_name", ""))
                    else:
                        result = {"status": "error", "message": f"Tool '{func_name}' not recognized."}

                    self.after(0, lambda fn=func_name, fa=func_args, res=result: self._add_tool_event_card(fn, fa, res))

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": json.dumps(result)
                    })

            self.after(0, lambda: self._update_status("● [SYS.ONLINE]", is_error=False))

            # Send any screenshots taken during tool execution directly to Telegram chat
            for shot_path in captured_screenshots:
                send_telegram_photo(
                    self.telegram_token,
                    chat_id,
                    shot_path,
                    caption=f"⚡ JARVIS 2.0 • Desktop Screen Capture [{self._get_timestamp()}]"
                )

            # Send AI text response back to Telegram
            if final_spoken_text:
                send_telegram_message(self.telegram_token, chat_id, final_spoken_text)

            # Trigger Text-to-Speech audio speech locally on PC if enabled
            if final_spoken_text and self.voice_enabled:
                threading.Thread(
                    target=self._speak_text_thread,
                    args=(final_spoken_text,),
                    daemon=True
                ).start()

        except Exception as ex:
            logger.exception("Telegram command error:")
            send_telegram_message(self.telegram_token, chat_id, f"❌ Command execution error: {str(ex)}")
            self.after(0, lambda: self._update_status("● [SYS.ONLINE]", is_error=False))

    # --------------------------------------------------------------------------
    # VISION-BASED AUTONOMOUS GUI AGENT ORCHESTRATOR
    # --------------------------------------------------------------------------

    def _set_vision_running_ui(self, is_running: bool):
        """Toggles the UI between standard chat mode and active Autonomous GUI mode."""
        def apply():
            if is_running:
                self.abort_btn.pack(side="left", padx=(0, 6))
                self.clear_btn.pack_forget()
                self._update_status("● [AUTO.VISION ACTIVE]", is_active=True)
                self.msg_entry.configure(state="disabled")
                self.send_btn.configure(state="disabled")
            else:
                self.abort_btn.pack_forget()
                self.clear_btn.pack(side="left")
                self._update_status("● [SYS.ONLINE]", is_error=False)
                self.msg_entry.configure(state="normal")
                self.send_btn.configure(state="normal")
                self.msg_entry.focus_set()
        self.after(0, apply)

    def _on_abort_clicked(self):
        """Immediately signals the atomic abort event and halts the vision loop."""
        if self.is_vision_running:
            logger.warning("Operator triggered emergency stop for Autonomous GUI sequence.")
            self.vision_abort_event.set()
            self._update_status("● [ABORTING...]", is_error=True)
            self._add_system_notice("🛑 [ABORT] Operator triggered emergency stop for Autonomous GUI Agent.")
            if self.voice_enabled:
                threading.Thread(
                    target=self._speak_text_thread,
                    args=("Autonomous GUI sequence aborted by operator.",),
                    daemon=True
                ).start()

    def _start_autonomous_gui_agent(self, goal: str, source: str = "desktop", chat_id: Optional[int] = None):
        """Starts a background daemon thread for the Vision Autonomous GUI Agent."""
        if self.is_vision_running:
            self._add_system_notice("⚠️ An autonomous GUI task is already running. Click ABORT to cancel it.")
            return

        self.is_vision_running = True
        self.vision_abort_event.clear()
        self._set_vision_running_ui(True)

        self.active_vision_thread = threading.Thread(
            target=self._run_autonomous_gui_loop,
            args=(goal, self.max_vision_steps, source, chat_id),
            daemon=True
        )
        self.active_vision_thread.start()

    def _deploy_autonomous_gui_from_tool(self, goal: str, source: str = "desktop", chat_id: Optional[int] = None) -> Dict[str, Any]:
        """Tool dispatcher callback invoked when the Groq LLM tool-calls run_autonomous_gui_agent."""
        if self.is_vision_running:
            return {
                "status": "error",
                "message": "An autonomous GUI sequence is already active on this desktop."
            }

        self.is_vision_running = True
        self.vision_abort_event.clear()
        self._set_vision_running_ui(True)

        # Run synchronously on the already-background worker thread of _process_message_thread
        return self._run_autonomous_gui_loop(goal=goal, max_steps=self.max_vision_steps, source=source, chat_id=chat_id)

    def _run_autonomous_gui_loop(
        self,
        goal: str,
        max_steps: int = MAX_AUTONOMOUS_STEPS,
        source: str = "desktop",
        chat_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes the production-ready Perception-Action loop for Windows UI Automation.
        Defensively handles:
        - Groq Free Tier 429 Rate Shield (exponential backoff with jitter + retry-after header parsing)
        - Step throttling (time.sleep(3.5)) to stay below TPM/RPM ceilings
        - Image compression (1280px max downscaling, 75% quality JPEG, Base64 data URLs)
        - Hybrid fast-path (deterministic shortcuts first, vision second)
        - Coordinate normalization, visual grid grounding, and strict JSON validation
        - PyAutoGUI guardrails (failsafe corner abort, unicode clipboard pasting, max 10 steps timeout)
        - Non-blocking state management, thumbnail timeline logging, and voice notifications.
        """
        logger.info(f"Initiating Vision-based Autonomous GUI Agent for goal: '{goal}'")
        was_vision_off = not getattr(self, "is_vision_enabled", False)
        if was_vision_off:
            self.set_vision_state(True, reason=f"Auto-activated for task: '{goal[:30]}'")

        api_key = self.current_api_key or os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            err = "GROQ_API_KEY is not configured in .env file! Cannot deploy Vision Agent."
            self.after(0, lambda: self._add_error_bubble(err))
            self.is_vision_running = False
            self._set_vision_running_ui(False)
            return {"status": "error", "message": err}

        # Announce launch via Voice TTS
        start_spoken = f"Initiating autonomous visual sequence: {goal[:60]}."
        if self.voice_enabled:
            threading.Thread(target=self._speak_text_thread, args=(start_spoken,), daemon=True).start()

        self.after(0, lambda: self._add_system_notice(
            f"👁 [AUTO-GUI DEPLOYED]\nObjective: {goal}\nMax Steps: {max_steps} • Rate Shield: ACTIVE"
        ))

        # ----------------------------------------------------------------------
        # 1. HYBRID FAST-PATH: SHORTCUTS FIRST, VISION SECOND
        # ----------------------------------------------------------------------
        fast_path_res = execute_hybrid_fast_path(goal)
        if fast_path_res.get("fast_path_used"):
            fp_notice = f"⚡ Fast-Path Shortcut Executed: {fast_path_res.get('message')}"
            self.after(0, lambda m=fp_notice: self._add_system_notice(m))
            if source == "telegram" and chat_id:
                send_telegram_message(self.telegram_token, chat_id, fp_notice)

            if fast_path_res.get("completed", False):
                # Target achieved deterministically; skip vision loop entirely to conserve tokens
                final_message = fast_path_res.get("message")
                is_completed = True
                self.is_vision_running = False
                self._set_vision_running_ui(False)
                if was_vision_off:
                    self.set_vision_state(False, reason="Fast-path completed, conserving Groq tokens")
                return {
                    "status": "success",
                    "steps_executed": 0,
                    "is_completed": True,
                    "message": final_message
                }
            # Allow window/browser page to render before visual inspection
            time.sleep(2.5)

        client = Groq(api_key=api_key)
        history_summary = []
        is_completed = False
        step = 0
        final_message = ""

        # ----------------------------------------------------------------------
        # 2. PERCEPTION-ACTION ITERATION LOOP (MAX 10 STEPS)
        # ----------------------------------------------------------------------
        while step < max_steps:
            step += 1

            # Check atomic abort event before starting step
            if self.vision_abort_event.is_set():
                logger.info("Autonomous GUI loop terminated via atomic abort event.")
                break

            # Step Throttling (3.5s) to protect Groq Free Tier TPM/RPM ceiling
            self.after(0, lambda s=step: self._update_status(f"● [STEP {s}/{max_steps}: THROTTLING...]", is_active=True))
            throttle_start = time.time()
            while time.time() - throttle_start < STEP_THROTTLE_SECONDS:
                if self.vision_abort_event.is_set():
                    break
                time.sleep(0.2)

            if self.vision_abort_event.is_set():
                break

            # ------------------------------------------------------------------
            # PERCEPTION: SCREEN CAPTURE & COMPRESSION (MAX 1280px, 75% JPEG)
            # ------------------------------------------------------------------
            self.after(0, lambda s=step: self._update_status(f"● [STEP {s}/{max_steps}: PERCEIVING...]", is_active=True))
            try:
                prep = prepare_vision_screenshot(max_width=VISION_COMPRESSION_WIDTH, quality=VISION_COMPRESSION_QUALITY)
            except Exception as cap_err:
                logger.error(f"Failed to capture screen during step {step}: {cap_err}")
                self.after(0, lambda e=str(cap_err): self._add_error_bubble(f"Screenshot capture failed: {e}"))
                final_message = f"Screen capture error at step {step}: {str(cap_err)}"
                break

            # ------------------------------------------------------------------
            # VISUAL GRID GROUNDING & PROMPT CONSTRUCTION
            # ------------------------------------------------------------------
            sys_prompt = VISION_AGENT_SYSTEM_PROMPT.format(width=prep["down_w"], height=prep["down_h"])
            hist_text = "\n".join([f"- Step {h['step']}: {h['action']} -> {h['thought']}" for h in history_summary[-3:]]) if history_summary else "None (Initial Step)"

            user_content = [
                {
                    "type": "text",
                    "text": (
                        f"USER OBJECTIVE: {goal}\n"
                        f"PREVIOUS ACTIONS:\n{hist_text}\n"
                        f"CURRENT SCREEN DIMENSIONS: {prep['down_w']}x{prep['down_h']} pixels.\n"
                        "Visually inspect the screenshot and return the single next action in strictly valid JSON format."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": prep["data_url"]}
                }
            ]

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content}
            ]

            # ------------------------------------------------------------------
            # RATE-LIMIT SHIELD: EXPONENTIAL BACKOFF + JITTER (4 RETRIES)
            # ------------------------------------------------------------------
            self.after(0, lambda s=step: self._update_status(f"● [STEP {s}/{max_steps}: INFERENCE...]", is_active=True))
            api_res = call_groq_vision_with_rate_shield(
                client=client,
                model=self.selected_vision_model,
                messages=messages,
                max_retries=4,
                abort_event=self.vision_abort_event,
                on_retry_callback=lambda msg: self.after(0, lambda m=msg: self._update_status(m, is_active=True))
            )

            if api_res.get("status") == "aborted":
                break

            if api_res.get("status") != "success":
                err_text = api_res.get("message", "Vision API inference failed.")
                self.after(0, lambda et=err_text: self._add_error_bubble(f"Vision API Error: {et}"))
                if source == "telegram" and chat_id:
                    send_telegram_message(self.telegram_token, chat_id, f"❌ Vision Error: {err_text}")
                final_message = err_text
                break

            # ------------------------------------------------------------------
            # STRICT JSON PARSING & VALIDATION
            # ------------------------------------------------------------------
            raw_content = api_res.get("content", "{}")
            try:
                # Strip markdown codeblocks if accidentally included
                clean_json = raw_content.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```[a-zA-Z]*\n?", "", clean_json)
                    clean_json = re.sub(r"\n?```$", "", clean_json)
                action_data = json.loads(clean_json)
            except json.JSONDecodeError as jde:
                logger.error(f"Failed to parse vision model JSON on step {step}: {jde}\nRaw: {raw_content}")
                self.after(0, lambda s=step: self._add_error_bubble(f"Step {s}: Model returned invalid JSON. Retrying visual inspection."))
                continue

            thought = str(action_data.get("thought", "")).strip()
            action = str(action_data.get("action", "")).lower().strip()
            x = action_data.get("x")
            y = action_data.get("y")
            text_arg = action_data.get("text")
            key_arg = action_data.get("key")
            is_completed = bool(action_data.get("is_completed", False)) or (action == "finish")

            # Validate coordinate boundaries relative to compressed image
            if action in ["click", "type"] and (x is not None and y is not None):
                try:
                    cx = float(x)
                    cy = float(y)
                    if cx < 0 or cx > prep["down_w"] or cy < 0 or cy > prep["down_h"]:
                        logger.warning(f"Coordinates ({cx}, {cy}) outside image dimensions ({prep['down_w']}x{prep['down_h']}). Clamping safely.")
                        action_data["x"] = max(0, min(prep["down_w"], cx))
                        action_data["y"] = max(0, min(prep["down_h"], cy))
                except (ValueError, TypeError):
                    pass

            # Format action summary string for UI
            if action == "click":
                action_str = f"CLICK at ({x}, {y})"
            elif action == "type":
                action_str = f"TYPE '{text_arg}' at ({x}, {y})" + (f" then press '{key_arg}'" if key_arg else "")
            elif action == "press":
                action_str = f"PRESS key '{key_arg}'"
            elif action == "scroll":
                action_str = f"SCROLL {action_data.get('direction', 'down')}"
            elif action == "wait":
                action_str = "WAIT 1.5s"
            elif action == "finish":
                action_str = "OBJECTIVE ACHIEVED"
            else:
                action_str = f"{action.upper()}"

            # Log step card with compressed thumbnail to Chat Timeline
            thumb_p = prep.get("thumb_path")
            self.after(0, lambda s=step, ms=max_steps, th=thought, act=action_str, tp=thumb_p: self._add_vision_step_card(s, ms, th, act, tp))

            # Broadcast step progress to Telegram if triggered remotely
            if source == "telegram" and chat_id:
                tg_step = f"👁 [Step {step}/{max_steps}] {action_str}\n🧠 {thought}"
                send_telegram_message(self.telegram_token, chat_id, tg_step)

            history_summary.append({
                "step": step,
                "action": action_str,
                "thought": thought
            })

            # Check for objective completion
            if is_completed:
                logger.info(f"Vision Agent accomplished goal at step {step}!")
                final_message = f"⚡ Objective completed successfully in {step} visual steps."
                self.after(0, lambda: self._add_ai_message(final_message))
                if source == "telegram" and chat_id:
                    fin_shot = capture_screenshot()
                    send_telegram_photo(self.telegram_token, chat_id, fin_shot, caption=f"✅ Task Completed: {goal}")
                if self.voice_enabled:
                    threading.Thread(target=self._speak_text_thread, args=("Objective achieved successfully, sir.",), daemon=True).start()
                break

            # ------------------------------------------------------------------
            # ACTION EXECUTION VIA PYAUTOGUI & PYPERCLIP
            # ------------------------------------------------------------------
            try:
                outcome = execute_gui_action(action_data, prep["scale_x"], prep["scale_y"], prep["orig_w"], prep["orig_h"])
                logger.info(f"Step {step} execution outcome: {outcome}")
            except pyautogui.FailSafeException:
                logger.warning("Emergency PyAutoGUI FailSafe triggered by moving cursor to corner!")
                self.vision_abort_event.set()
                self.after(0, lambda: self._add_system_notice("🛑 [FAILSAFE TRIGGERED] Cursor moved to screen corner. Sequence aborted."))
                if self.voice_enabled:
                    threading.Thread(target=self._speak_text_thread, args=("Failsafe triggered. Autonomous control aborted.",), daemon=True).start()
                final_message = "Aborted by mouse corner failsafe."
                break
            except Exception as act_err:
                logger.error(f"Step {step} GUI execution error: {act_err}")
                self.after(0, lambda ae=str(act_err): self._add_error_bubble(f"Action Execution Error: {ae}"))

        # ----------------------------------------------------------------------
        # 3. POST-LOOP FINALIZATION (SUCCESS, ABORT, OR TIMEOUT)
        # ----------------------------------------------------------------------
        if self.vision_abort_event.is_set():
            final_message = "Autonomous GUI sequence aborted by operator."
            self.after(0, lambda: self._add_system_notice("🛑 [AUTO-GUI ABORTED] Autonomous sequence cancelled by operator."))
            if source == "telegram" and chat_id:
                send_telegram_message(self.telegram_token, chat_id, "🛑 Autonomous GUI sequence aborted by operator.")
        elif step >= max_steps and not is_completed:
            logger.warning(f"Autonomous GUI Agent timed out after {max_steps} steps.")
            final_screen = capture_screenshot()
            timeout_msg = f"⚠️ [AUTO-GUI TIMEOUT] Sequence reached maximum threshold ({max_steps} steps). Control returned to operator."
            self.after(0, lambda m=timeout_msg: self._add_system_notice(m))
            if source == "telegram" and chat_id:
                send_telegram_photo(self.telegram_token, chat_id, final_screen, caption=f"⚠️ Autonomous GUI Timeout ({max_steps} steps): {goal}")
            if self.voice_enabled:
                threading.Thread(target=self._speak_text_thread, args=("Autonomous task reached maximum step limit without completion, sir.",), daemon=True).start()
            final_message = f"Sequence reached maximum threshold ({max_steps} steps) without completion."

        self.is_vision_running = False
        self._set_vision_running_ui(False)
        if was_vision_off:
            self.set_vision_state(False, reason="Task completed, conserving Groq tokens")

        return {
            "status": "success" if is_completed else ("aborted" if self.vision_abort_event.is_set() else "timeout"),
            "steps_executed": step,
            "is_completed": is_completed,
            "message": final_message
        }


# ==============================================================================
# ENTRYPOINT
# ==============================================================================

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    app = GroqDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
