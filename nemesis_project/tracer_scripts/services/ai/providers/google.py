"""
NEMESIS AI FABRIC v3.1
Google AI Stack Provider (Gemini / Vertex)
"""

import os
import logging
from typing import Dict, Any
from tracer_scripts.services.ai.providers.base import AIProvider
from tracer_scripts.services.ai.capability_matrix import ModelProvider

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger("AIFabric.Providers.Google")

class GoogleProvider(AIProvider):
    def __init__(self):
        self.api_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
        self.api_key = self.api_keys[0].strip() if self.api_keys and self.api_keys[0] else None
        self.client = genai.Client(api_key=self.api_key) if HAS_GENAI and self.api_key else None

    async def execute(self, model: ModelProvider, prompt: str, system_instruction: str = "", **kwargs) -> str:
        if not self.client:
            raise RuntimeError("Google GenAI client not initialized. Missing API Key.")
            
        # Map the enum to the actual string ID
        model_id = model.value
        if model == ModelProvider.GEMINI_DEEP_THINK:
            model_id = "gemini-2.0-pro-exp-02-05" # Assuming deep think preview model
            
        config = types.GenerateContentConfig(
            system_instruction=system_instruction if system_instruction else None,
            temperature=kwargs.get("temperature", 0.0),
        )
        
        # We use the sync generate_content inside an async wrapper (or run_in_executor in production)
        response = self.client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=config
        )
        return response.text

    async def get_health_status(self) -> Dict[str, Any]:
        if not self.client:
            return {"status": "failing", "error": "No API Key"}
        return {"status": "healthy", "provider": "Google GenAI"}
