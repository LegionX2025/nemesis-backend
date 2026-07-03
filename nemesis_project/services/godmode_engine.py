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
        if not self.gemini_key:
            await self.broadcast("> [FATAL] GEMINI_API_KEY NOT CONFIGURED. CANNOT HEAL.")
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
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        
        try:
            # We use an executor because requests is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=payload))
            response.raise_for_status()
            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean up markdown if the LLM hallucinated it
            if text.startswith("```python"):
                text = text[9:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            text = text.strip()
            
            await self.broadcast(f"> [GODMODE] Patch generated:\n```python\n{text}\n```")
            return text
        except Exception as e:
            await self.broadcast(f"> [GODMODE] Failed to generate patch: {e}")
            return None

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
