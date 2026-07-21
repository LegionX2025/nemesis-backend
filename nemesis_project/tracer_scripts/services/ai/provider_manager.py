"""
NEMESIS AI FABRIC v3.1
Provider Manager
Maps ModelProvider Enums to their concrete execution adapters.
"""

import logging
from typing import Dict, Any
from tracer_scripts.services.ai.capability_matrix import ModelProvider
from tracer_scripts.services.ai.providers.base import AIProvider
from tracer_scripts.services.ai.providers.google import GoogleProvider

logger = logging.getLogger("AIFabric.ProviderManager")

class MockProvider(AIProvider):
    """Stub provider for unconfigured or pending AI Stacks."""
    async def execute(self, model: ModelProvider, prompt: str, system_instruction: str = "", **kwargs) -> str:
        logger.warning(f"Using MockProvider for {model.value}")
        return f"[Simulated Output from {model.value}] Processed dynamically classified task."

    async def get_health_status(self) -> Dict[str, Any]:
        return {"status": "healthy", "provider": "MockProvider"}

class ProviderManager:
    def __init__(self):
        # Initialize configured providers
        self.google = GoogleProvider()
        self.mock = MockProvider()
        
    def get_provider(self, model: ModelProvider) -> AIProvider:
        """Returns the appropriate adapter instance for the model."""
        if model.value.startswith("gemini"):
            return self.google
        elif model.value.startswith("gpt"):
            return self.mock # OpenAIProvider pending
        elif model.value.startswith("claude"):
            return self.mock # AnthropicProvider pending
        elif model.value.startswith("deepseek"):
            return self.mock # DeepSeekProvider pending
        elif model.value.startswith("mistral") or model == ModelProvider.CODESTRAL:
            return self.mock # MistralProvider pending
        elif model == ModelProvider.LOCAL_VLLM:
            return self.mock # LocalVLLMProvider pending
            
        return self.mock

provider_manager = ProviderManager()
