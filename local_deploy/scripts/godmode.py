import asyncio
import logging
import json
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from google import genai

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NEMESIS_OS_KERNEL")

class NemesisKernel:
    def __init__(self):
        self.root = Path(".").resolve()
        # The Hybrid State Registry: Tracks paradigm-specific states
        self.state_layers = {
            "kernel": "FSM",
            "agents": "HSM_BehaviorTree",
            "investigation": "Workflow",
            "intelligence": "Dataflow",
            "security": "RuleBased"
        }
        gemini_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=gemini_keys.split(",")[0].strip() if gemini_keys else None)
        self.model_name = 'gemini-3.0-preview'

    # --- HYBRID STATE DISPATCHER ---
    async def dispatch(self, layer, module, event):
        """Routes logic to the correct State Machine paradigm."""
        logger.info(f"[LAYER: {layer}] Module: {module} | Event: {event}")
        
        # Example: Using Dataflow for Intelligence
        if layer == "intelligence":
            await self._run_dataflow(module, event)
        # Example: Using Behavior Tree for Agents
        elif layer == "agents":
            await self._run_behavior_tree(module, event)
        # Fallback to general dispatch
        else:
            await self._run_fsm(module, event)

    # --- PARADIGM HANDLERS ---
    async def _run_dataflow(self, module, event):
        # Implementation of Dataflow (Ingest -> Normalize -> Enrich -> Publish)
        logger.info(f"[*] Executing Dataflow logic for {module}...")

    async def _run_behavior_tree(self, module, event):
        # Implementation of Behavior Tree (Check -> Selector -> Action)
        logger.info(f"[*] Traversing Behavior Tree for {module}...")

    async def _run_fsm(self, module, event):
        # Classic FSM transition logic
        logger.info(f"[*] FSM Transition: {module} moved to {event}...")

    # --- COGNITIVE ENGINE ---
    async def cognitive_cycle(self):
        while True:
            # The "God Mode" loop asks the AI to evaluate which state layer 
            # should handle the next mission priority.
            prompt = f"""
            System States Layers: {json.dumps(self.state_layers)}
            Mission: Autonomous Forensics.
            
            1. Select current priority layer (e.g., 'intelligence', 'agents').
            2. Infer next required state transition.
            3. Return JSON: {{"layer": "...", "module": "...", "event": "..."}}
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            try:
                decision = json.loads(response.text.replace('```json', '').replace('```', ''))
                await self.dispatch(decision['layer'], decision['module'], decision['event'])
            except Exception as e:
                logger.error(f"[!] Hybrid Dispatcher Error: {e}")
            
            await asyncio.sleep(5)

if __name__ == "__main__":
    kernel = NemesisKernel()
    asyncio.run(kernel.cognitive_cycle())