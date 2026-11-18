"""
==============================================================================
JARVIS 2.0 - Web Backend Server (21st.dev UI Edition)
==============================================================================
Provides high-performance REST APIs connecting modern 21st.dev Web UI
to Windows desktop controls, Groq Tool Calling, hardware health telemetry,
and Edge Neural TTS voice playback.
==============================================================================
"""

import os
import sys
import json
import time
import logging
import threading
import webbrowser
from typing import Dict, Any, List

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Import battle-tested core modules from app.py
import app

# Resolve and load environment
app.resolve_and_load_env()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS-SERVER")

server_app = Flask(__name__, static_folder="web")
CORS(server_app)

# Global Runtime State
state = {
    "model_name": app.DEFAULT_MODELS[0],
    "is_vision_enabled": False,
    "voice_enabled": True,
    "voice_rate": 180,
    "selected_english_persona": "J.A.R.V.I.S. (British Male • Iron Man)",
    "selected_tamil_persona": "Pallavi (Female • India)",
    "default_voice_language": os.getenv("DEFAULT_VOICE_LANGUAGE", "english").lower(),
    "welcome_language": os.getenv("WELCOME_LANGUAGE", "english").lower(),
    "custom_welcome_message": os.getenv("CUSTOM_WELCOME_MESSAGE", "").strip(),
    "is_speaking": False,
    "current_speech_type": "none",
}

conversation_history: List[Dict[str, Any]] = [
    {"role": "system", "content": app.SYSTEM_PROMPT}
]

# Audio speech helper
def play_speech_background(text: str):
    """Speaks text using Edge Neural TTS or pyttsx3 fallback."""
    if not state["voice_enabled"] or not text.strip():
        return

    cleaned = app.clean_for_speech(text)
    if not cleaned:
        return

    state["is_speaking"] = True
    is_tamil = (state["default_voice_language"] == "tamil") or app.is_tamil_or_tanglish(cleaned)
    state["current_speech_type"] = "tamil" if is_tamil else "english"

    def _worker():
        try:
            if is_tamil:
                voice_name = app.TAMIL_VOICES.get(state["selected_tamil_persona"], "ta-IN-PallaviNeural")
            else:
                voice_name = app.ENGLISH_VOICES.get(state["selected_english_persona"], "en-GB-RyanNeural")

            success = False
            if app.edge_tts is not None and app.pygame is not None:
                # Helper synthesis via Edge TTS
                import tempfile
                import asyncio
                async def _synth():
                    comm = app.edge_tts.Communicate(cleaned, voice_name)
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                        p = fp.name
                    await comm.save(p)
                    return p

                temp_path = None
                try:
                    temp_path = asyncio.run(_synth())
                    if not app.pygame.mixer.get_init():
                        app.pygame.mixer.init()
                    app.pygame.mixer.music.load(temp_path)
                    app.pygame.mixer.music.play()
                    while app.pygame.mixer.music.get_busy() and state["is_speaking"]:
                        app.pygame.time.Clock().tick(15)
                    app.pygame.mixer.music.stop()
                    app.pygame.mixer.quit()
                    success = True
                except Exception as ex:
                    logger.warning(f"Edge TTS error in server: {ex}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

            if not success and app.pyttsx3 is not None:
                try:
                    engine = app.pyttsx3.init()
                    engine.setProperty("rate", state["voice_rate"])
                    engine.say(cleaned)
                    engine.runAndWait()
                except Exception as ex:
                    logger.warning(f"Fallback pyttsx3 error: {ex}")
        finally:
            state["is_speaking"] = False
            state["current_speech_type"] = "none"

    threading.Thread(target=_worker, daemon=True).start()

def stop_active_speech():
    """Stops any currently playing audio speech."""
    state["is_speaking"] = False
    state["current_speech_type"] = "none"
    try:
        if app.pygame and app.pygame.mixer.get_init():
            app.pygame.mixer.music.stop()
            app.pygame.mixer.quit()
    except Exception:
        pass

# ------------------------------------------------------------------------------
# STATIC ROUTES
# ------------------------------------------------------------------------------

@server_app.route("/")
def index():
    return send_from_directory("web", "index.html")

@server_app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join("web", path)):
        return send_from_directory("web", path)
    return send_from_directory("web", "index.html")

# ------------------------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------------------------

@server_app.route("/api/status", methods=["GET"])
def get_status():
    """Returns general server status and active configuration."""
    api_key_set = bool(os.getenv("GROQ_API_KEY", "").strip())
    return jsonify({
        "status": "online",
        "api_key_configured": api_key_set,
        "model": state["model_name"],
        "models_available": app.DEFAULT_MODELS,
        "is_vision_enabled": state["is_vision_enabled"],
        "voice_enabled": state["voice_enabled"],
        "is_speaking": state["is_speaking"],
        "current_speech_type": state["current_speech_type"],
        "default_voice_language": state["default_voice_language"]
    })

@server_app.route("/api/health", methods=["GET"])
def get_health_telemetry():
    """Returns live hardware & OS health telemetry (CPU, RAM, Disk, Power, Processes)."""
    telemetry = app.get_system_health()
    return jsonify(telemetry)

@server_app.route("/api/apps", methods=["GET"])
def get_running_apps():
    """Returns the list of active running desktop applications."""
    result = app.list_running_applications()
    return jsonify(result)

weather_cache = {"timestamp": 0, "data": None}

@server_app.route("/api/weather", methods=["GET"])
def get_weather_telemetry():
    """Returns live atmospheric & weather telemetry with local caching."""
    global weather_cache
    now = time.time()
    if weather_cache["data"] and (now - weather_cache["timestamp"] < 600):
        return jsonify(weather_cache["data"])

    try:
        import urllib.request
        req = urllib.request.Request("https://wttr.in/?format=j1", headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            curr = data["current_condition"][0]
            area = data["nearest_area"][0]
            forecast_list = []
            for day in data.get("weather", [])[:5]:
                forecast_list.append({
                    "date": day.get("date", ""),
                    "max_c": day.get("maxtempC", "30"),
                    "min_c": day.get("mintempC", "22"),
                    "desc": day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "Clear") if len(day.get("hourly", [])) > 4 else "Clear"
                })

            weather_payload = {
                "status": "success",
                "city": area["areaName"][0]["value"],
                "country": area["country"][0]["value"],
                "temp_c": curr["temp_C"],
                "feels_like_c": curr.get("FeelsLikeC", curr["temp_C"]),
                "humidity": curr.get("humidity", "60"),
                "wind_kmph": curr.get("windspeedKmph", "10"),
                "visibility_km": curr.get("visibility", "10"),
                "pressure_hpa": curr.get("pressure", "1012"),
                "condition": curr["weatherDesc"][0]["value"],
                "forecast": forecast_list
            }
            weather_cache["timestamp"] = now
            weather_cache["data"] = weather_payload
            return jsonify(weather_payload)
    except Exception as ex:
        logger.debug(f"Weather lookup fallback: {ex}")
        fallback_payload = {
            "status": "fallback",
            "city": "Local Station",
            "country": "Grid 01",
            "temp_c": "28",
            "feels_like_c": "29",
            "humidity": "62",
            "wind_kmph": "12",
            "visibility_km": "10",
            "pressure_hpa": "1013",
            "condition": "Atmosphere Stable",
            "forecast": [
                {"date": "Day 1", "max_c": "30", "min_c": "22", "desc": "Clear"},
                {"date": "Day 2", "max_c": "31", "min_c": "23", "desc": "Partly Cloudy"},
                {"date": "Day 3", "max_c": "29", "min_c": "21", "desc": "Mild"},
                {"date": "Day 4", "max_c": "30", "min_c": "22", "desc": "Clear"},
                {"date": "Day 5", "max_c": "28", "min_c": "20", "desc": "Overcast"}
            ]
        }
        return jsonify(fallback_payload)

@server_app.route("/api/chat", methods=["POST"])
def chat_completion():
    """Processes user chat input with Groq Tool Calling, tool execution, and voice speech."""
    data = request.get_json() or {}
    user_prompt = (data.get("message") or "").strip()
    if not user_prompt:
        return jsonify({"status": "error", "message": "Empty message prompt."}), 400

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return jsonify({
            "status": "error",
            "message": "GROQ_API_KEY is not configured in .env file! Please configure it in Settings."
        }), 400

    model = data.get("model") or state["model_name"]
    state["model_name"] = model

    # Stop any ongoing speech when user enters a new message
    stop_active_speech()

    # Append user input
    conversation_history.append({"role": "user", "content": user_prompt})

    tool_events: List[Dict[str, Any]] = []
    final_spoken_text = ""
    ai_response_text = ""

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        max_rounds = 5
        round_idx = 0

        while round_idx < max_rounds:
            round_idx += 1

            response = client.chat.completions.create(
                model=model,
                messages=conversation_history,
                tools=app.TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2048
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                ai_response_text = response_message.content or "Command completed."
                final_spoken_text = ai_response_text
                conversation_history.append({"role": "assistant", "content": ai_response_text})
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
            conversation_history.append(assistant_record)

            for tc in tool_calls:
                func_name = tc.function.name
                func_args_raw = tc.function.arguments or "{}"
                try:
                    func_args = json.loads(func_args_raw)
                except Exception:
                    func_args = {"raw": func_args_raw}

                # Execute tool
                if func_name == "get_system_health":
                    tool_result = app.get_system_health()
                elif func_name == "list_running_applications":
                    tool_result = app.list_running_applications()
                elif func_name == "open_application":
                    tool_result = app.open_application(func_args.get("app_name", ""))
                elif func_name == "close_application":
                    tool_result = app.close_application(func_args.get("app_name", ""))
                elif func_name == "open_website":
                    tool_result = app.open_website(func_args.get("url", ""))
                elif func_name == "execute_command":
                    tool_result = app.execute_command(
                        command=func_args.get("command", ""),
                        shell_type=func_args.get("shell_type", "powershell")
                    )
                elif func_name == "take_screenshot":
                    tool_result = app.take_screenshot(func_args.get("filename"))
                elif func_name == "set_vision_state":
                    new_val = func_args.get("enabled", False)
                    state["is_vision_enabled"] = new_val
                    tool_result = {
                        "status": "success",
                        "enabled": new_val,
                        "message": f"Vision state set to {'ON' if new_val else 'OFF'}."
                    }
                else:
                    tool_result = {"status": "error", "message": f"Tool '{func_name}' is not recognized."}

                tool_events.append({
                    "tool": func_name,
                    "args": func_args,
                    "result": tool_result
                })

                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": func_name,
                    "content": json.dumps(tool_result)
                })

        # Trigger voice speech synthesis on server
        if final_spoken_text and state["voice_enabled"]:
            play_speech_background(final_spoken_text)

        is_tamil = app.is_tamil_or_tanglish(ai_response_text)

        return jsonify({
            "status": "success",
            "response": ai_response_text,
            "spoken_text": app.clean_for_speech(ai_response_text),
            "tool_events": tool_events,
            "is_tamil": is_tamil,
            "is_speaking": state["is_speaking"]
        })

    except Exception as ex:
        logger.error(f"Error during chat completion: {ex}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(ex)
        }), 500

@server_app.route("/api/speak", methods=["POST"])
def trigger_speech():
    """Triggers speech synthesis for arbitrary text."""
    data = request.get_json() or {}
    text = data.get("text", "")
    play_speech_background(text)
    return jsonify({"status": "success", "message": "Speech started."})

@server_app.route("/api/stop_speech", methods=["POST"])
def stop_speech_endpoint():
    """Immediately stops audio speech playback."""
    stop_active_speech()
    return jsonify({"status": "success", "message": "Speech stopped."})

@server_app.route("/api/vision/toggle", methods=["POST"])
def toggle_vision():
    """Toggles vision perception state."""
    state["is_vision_enabled"] = not state["is_vision_enabled"]
    return jsonify({
        "status": "success",
        "is_vision_enabled": state["is_vision_enabled"]
    })

@server_app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    """Reads or updates application configuration."""
    if request.method == "GET":
        api_key = os.getenv("GROQ_API_KEY", "")
        masked_key = (api_key[:6] + "..." + api_key[-4:]) if len(api_key) > 10 else ("Configured" if api_key else "Missing")
        return jsonify({
            "model_name": state["model_name"],
            "models_available": app.DEFAULT_MODELS,
            "vision_models": app.VISION_MODELS,
            "voice_enabled": state["voice_enabled"],
            "voice_rate": state["voice_rate"],
            "english_voices": list(app.ENGLISH_VOICES.keys()),
            "selected_english_persona": state["selected_english_persona"],
            "tamil_voices": list(app.TAMIL_VOICES.keys()),
            "selected_tamil_persona": state["selected_tamil_persona"],
            "default_voice_language": state["default_voice_language"],
            "welcome_language": state["welcome_language"],
            "custom_welcome_message": state["custom_welcome_message"],
            "groq_api_key_masked": masked_key,
            "telegram_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
        })

    # POST: Update settings
    payload = request.get_json() or {}
    if "groq_api_key" in payload and payload["groq_api_key"].strip():
        app.save_env_variable("GROQ_API_KEY", payload["groq_api_key"].strip())
    if "telegram_token" in payload and payload["telegram_token"].strip():
        app.save_env_variable("TELEGRAM_BOT_TOKEN", payload["telegram_token"].strip())
    if "telegram_password" in payload and payload["telegram_password"].strip():
        app.save_env_variable("TELEGRAM_BOT_PASSWORD", payload["telegram_password"].strip())
    if "default_voice_language" in payload:
        state["default_voice_language"] = payload["default_voice_language"]
        app.save_env_variable("DEFAULT_VOICE_LANGUAGE", state["default_voice_language"])
    if "welcome_language" in payload:
        state["welcome_language"] = payload["welcome_language"]
        app.save_env_variable("WELCOME_LANGUAGE", state["welcome_language"])
    if "custom_welcome_message" in payload:
        state["custom_welcome_message"] = payload["custom_welcome_message"]
        app.save_env_variable("CUSTOM_WELCOME_MESSAGE", state["custom_welcome_message"])
    if "selected_english_persona" in payload:
        state["selected_english_persona"] = payload["selected_english_persona"]
    if "selected_tamil_persona" in payload:
        state["selected_tamil_persona"] = payload["selected_tamil_persona"]
    if "voice_enabled" in payload:
        state["voice_enabled"] = bool(payload["voice_enabled"])
    if "voice_rate" in payload:
        state["voice_rate"] = int(payload["voice_rate"])
    if "model_name" in payload:
        state["model_name"] = payload["model_name"]

    return jsonify({"status": "success", "message": "Configuration updated successfully."})

@server_app.route("/api/screenshot", methods=["POST"])
def take_screenshot_api():
    """Captures desktop screenshot with brief 150ms stabilization guardrail."""
    time.sleep(0.15)  # Vision safety freeze for crystal-clear capture
    res = app.take_screenshot()
    return jsonify(res)

desktop_window = None
is_window_maximized = False
saved_window_geom = {"x": 20, "y": 20, "w": 1240, "h": 680}

def get_work_area():
    """Gets the Windows Work Area excluding the Windows Taskbar."""
    try:
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        # SPI_GETWORKAREA = 0x0030 (48)
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
    except Exception as ex:
        logger.debug(f"Could not retrieve SPI_GETWORKAREA: {ex}")
    return 0, 0, 1366, 728

@server_app.route("/api/window/minimize", methods=["POST"])
def window_minimize():
    """Minimizes the native desktop WebView window."""
    global desktop_window
    if desktop_window:
        try:
            desktop_window.minimize()
            return jsonify({"status": "success"})
        except Exception as ex:
            return jsonify({"status": "error", "message": str(ex)}), 500
    return jsonify({"status": "ignored", "message": "Window instance not active."})

@server_app.route("/api/window/maximize", methods=["POST"])
def window_maximize():
    """Toggles maximize (fit to Windows work area without hiding taskbar) and restore."""
    global desktop_window, is_window_maximized, saved_window_geom
    if desktop_window:
        try:
            work_x, work_y, work_w, work_h = get_work_area()

            if not is_window_maximized:
                # Save previous geometry before maximizing
                try:
                    cur_w = desktop_window.width or 1240
                    cur_h = desktop_window.height or 680
                    cur_x = desktop_window.x if desktop_window.x is not None else 20
                    cur_y = desktop_window.y if desktop_window.y is not None else 20
                    saved_window_geom = {"x": cur_x, "y": cur_y, "w": cur_w, "h": cur_h}
                except Exception:
                    pass

                # Maximize directly into Windows Work Area (keeps Taskbar / PC footer bar 100% visible!)
                desktop_window.move(work_x, work_y)
                desktop_window.resize(work_w, work_h)
                is_window_maximized = True
                return jsonify({"status": "success", "is_maximized": True})
            else:
                # Restore to previous geometry
                restore_x = saved_window_geom.get("x", 20)
                restore_y = saved_window_geom.get("y", 20)
                restore_w = saved_window_geom.get("w", 1240)
                restore_h = saved_window_geom.get("h", 680)

                desktop_window.move(restore_x, restore_y)
                desktop_window.resize(restore_w, restore_h)
                is_window_maximized = False
                return jsonify({"status": "success", "is_maximized": False})
        except Exception as ex:
            logger.error(f"Error maximizing window: {ex}")
            return jsonify({"status": "error", "message": str(ex)}), 500
    return jsonify({"status": "ignored", "message": "Window instance not active."})

@server_app.route("/api/window/close", methods=["POST"])
def window_close():
    """Closes the desktop application window cleanly."""
    global desktop_window
    if desktop_window:
        try:
            desktop_window.destroy()
            return jsonify({"status": "success"})
        except Exception as ex:
            return jsonify({"status": "error", "message": str(ex)}), 500
    return jsonify({"status": "ignored", "message": "Window instance not active."})

@server_app.route("/api/clear", methods=["POST"])
def clear_conversation():
    """Resets the conversation history."""
    global conversation_history
    conversation_history = [{"role": "system", "content": app.SYSTEM_PROMPT}]
    return jsonify({"status": "success", "message": "Conversation history cleared."})

if __name__ == "__main__":
    port = 5000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    logger.info(f"Starting JARVIS 2.0 Web Server on {url} ...")

    # Start Flask server in background daemon thread
    flask_thread = threading.Thread(
        target=lambda: server_app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    # Brief delay for server socket binding
    time.sleep(0.5)

    # Launch native desktop WebView window (or fallback to browser if --browser flag passed)
    use_browser = "--browser" in sys.argv
    if not use_browser:
        try:
            import webview

            # Calculate HUD window placement fitting inside Windows Work Area (Taskbar stays visible)
            work_x, work_y, work_w, work_h = get_work_area()
            win_w = min(1320, work_w - 30)
            win_h = min(700, work_h - 24)
            pos_x = max(10, work_x + (work_w - win_w) // 2)
            pos_y = max(10, work_y + (work_h - win_h) // 2)
            saved_window_geom = {"x": pos_x, "y": pos_y, "w": win_w, "h": win_h}

            logger.info(f"Launching native desktop WebView window ({win_w}x{win_h} at +{pos_x}+{pos_y})...")
            desktop_window = webview.create_window(
                title="[JARVIS 2.0 • Iron Man MK-85 Holographic HUD]",
                url=url,
                width=win_w,
                height=win_h,
                x=pos_x,
                y=pos_y,
                resizable=True,
                frameless=True,
                easy_drag=False,
                min_size=(900, 520),
                background_color="#030712",
                text_select=True,
                zoomable=True
            )
            webview.start(debug=False)
            sys.exit(0)
        except Exception as ex:
            logger.warning(f"Could not open native WebView window ({ex}). Falling back to browser.")
            webbrowser.open(url)
            flask_thread.join()
    else:
        logger.info("Opening in default browser due to --browser flag...")
        webbrowser.open(url)
        flask_thread.join()

