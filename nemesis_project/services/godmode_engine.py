import os
import sys
import json
import asyncio
import requests
import subprocess
import logging
from typing import List
from fastapi import WebSocket
from dotenv import load_dotenv

logger = logging.getLogger("GodmodeEngine")
load_dotenv()

class GodmodeEngine:
    def __init__(self):
        self.auto_pilot_enabled = False
        self.active_connections: List[WebSocket] = []
        
        # Load API Key
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if self.gemini_key and "," in self.gemini_key:
            self.gemini_key = self.gemini_key.split(",")[0].strip()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_personal_message(f"> SYSTEM CONNECTED. AUTO-PILOT IS {'[ONLINE]' if self.auto_pilot_enabled else '[STANDBY]'}", websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception:
            pass

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass
                
    def toggle_autopilot(self, state: bool):
        self.auto_pilot_enabled = state
        return self.auto_pilot_enabled

    async def query_gemini_to_heal(self, error_log: str):
        # Load keys fresh just in case they were updated in env
        GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", ""))
        gemini_keys = [k.strip() for k in GEMINI_API_KEYS.split(",") if k.strip()]
        AIML_KEY = os.environ.get("AIML_API_KEY_BAGOODEX", os.environ.get("AIML_API_KEY_CHATGPT"))

        if not gemini_keys and not AIML_KEY:
            await self.broadcast("> [FATAL] NO API KEYS CONFIGURED (GEMINI OR AIML). CANNOT HEAL.")
            return None
            
        await self.broadcast(f"> [GODMODE] Analyzing error trace...\n> {error_log.splitlines()[-1] if error_log.strip() else 'Unknown error'}")
        await asyncio.sleep(1) # Dramatic pause for UI
        await self.broadcast("> [GODMODE] Querying Omni-Intelligence Cluster for patch...")

        prompt = f"""
You are the Godmode Self-Healing Agent running in a backend FastAPI server.
A runtime error just occurred in the Python application.
Here is the error log/traceback:

```text
{error_log}
```

Write a python script that will automatically fix this issue in the codebase.
For example, write a script to read the broken file, string replace the error, and rewrite it.

ONLY OUTPUT VALID PYTHON CODE. Do not include markdown code blocks (like ```python) in your response, just the raw python code. DO NOT OUTPUT ANYTHING ELSE.
        """
        
        loop = asyncio.get_event_loop()

        # Try Gemini Keys First
        for key in gemini_keys:
            if not key.startswith("AIza"): continue
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2}
            }
            try:
                response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=payload, timeout=15))
                if response.status_code == 429:
                    await self.broadcast(f"> [GODMODE] Gemini key {key[:8]}... rate limited. Rotating...")
                    continue
                response.raise_for_status()
                result = response.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return self._clean_script(text)
            except Exception as e:
                await self.broadcast(f"> [GODMODE] Failed with Gemini key {key[:8]}... : {e}")
                continue

        # Fallback to AIML Gateways
        if AIML_KEY:
            await self.broadcast("> [GODMODE] Falling back to AIML Gateways...")
            try:
                url = "https://api.aimlapi.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {AIML_KEY}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=payload, timeout=20))
                response.raise_for_status()
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                return self._clean_script(text)
            except Exception as e:
                await self.broadcast(f"> [GODMODE] AIML fallback failed: {e}")

        await self.broadcast("> [GODMODE] All AI healing models exhausted or failed.")
        return None

    def _clean_script(self, text):
        if text.startswith("```python"):
            text = text[9:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    async def heal_runtime_error(self, error_log: str):
        if not self.auto_pilot_enabled:
            logger.error("Godmode Auto-Pilot is OFF. Cannot self-heal.")
            return False

        await self.broadcast("\n> =========================================")
        await self.broadcast("> 🚨 CRITICAL RUNTIME ERROR DETECTED 🚨")
        await self.broadcast("> =========================================")
        await self.broadcast("> [GODMODE] Engaging Auto-Pilot Self-Repair Protocol...")
        
        fix_script = await self.query_gemini_to_heal(error_log)
        
        if fix_script:
            await self.broadcast("> [GODMODE] Applying patch to source code...")
            with open("godmode_runtime_fix.py", "w", encoding="utf-8") as f:
                f.write(fix_script)
                
            try:
                # Run the fix script
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "godmode_runtime_fix.py",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    await self.broadcast(f"> [GODMODE] Patch applied successfully! {stdout.decode()}")
                else:
                    await self.broadcast(f"> [GODMODE] Patch execution failed: {stderr.decode()}")
            except Exception as e:
                await self.broadcast(f"> [GODMODE] The healing patch failed to execute: {e}")
                
            if os.path.exists("godmode_runtime_fix.py"):
                os.remove("godmode_runtime_fix.py")
                
            await self.broadcast("> [GODMODE] Self-Healing Cycle Complete.")
            return True
        else:
            await self.broadcast("> [GODMODE] Omni-Intelligence could not provide a fix.")
            return False

godmode_engine = GodmodeEngine()
