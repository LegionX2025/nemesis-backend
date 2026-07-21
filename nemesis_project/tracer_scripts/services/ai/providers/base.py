"""
NEMESIS AI FABRIC v3.1
Base Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from tracer_scripts.services.ai.capability_matrix import ModelProvider

class AIProvider(ABC):
    """Abstract base class for all AI Fabric Providers."""
    
    @abstractmethod
    async def execute(self, model: ModelProvider, prompt: str, system_instruction: str = "", **kwargs) -> str:
        """Executes a prompt against the specific model and returns the text response."""
        pass
        
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """Ping the provider API to verify active keys and latency."""
        pass
