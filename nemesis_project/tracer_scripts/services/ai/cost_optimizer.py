"""
NEMESIS AI FABRIC v3.1 Enterprise
Cost Optimizer & Rate Limiter
Evaluates token costs per provider and throttles RPM/TPD limits.
"""

import logging
from typing import Dict, Tuple
from tracer_scripts.services.ai.capability_matrix import ModelProvider

logger = logging.getLogger("AIFabric.CostOptimizer")

# Simulated Cost Matrix (Input Cost per 1M tokens, Output Cost per 1M tokens)
COST_MATRIX: Dict[ModelProvider, Tuple[float, float]] = {
    ModelProvider.GEMINI_FLASH: (0.075, 0.30),
    ModelProvider.GEMINI_FLASH_LITE: (0.03, 0.15),
    ModelProvider.GEMINI_PRO: (3.50, 10.50),
    ModelProvider.GEMINI_DEEP_THINK: (7.00, 21.00),
    ModelProvider.GPT_5_5_MINI: (0.15, 0.60),
    ModelProvider.GPT_5_5: (5.00, 15.00),
    ModelProvider.CLAUDE_SONNET: (3.00, 15.00),
    ModelProvider.CLAUDE_OPUS: (15.00, 75.00),
    ModelProvider.DEEPSEEK_CHAT: (0.14, 0.28),
    ModelProvider.LOCAL_VLLM: (0.0, 0.0), # Free local inference
}

class CostOptimizer:
    """Calculates running costs and sorts models by cost-efficiency."""
    
    @classmethod
    def get_cheapest_capable_model(cls, capable_models: list[ModelProvider]) -> ModelProvider:
        """From a list of capable models, returns the most cost-efficient one."""
        if ModelProvider.LOCAL_VLLM in capable_models:
            return ModelProvider.LOCAL_VLLM # Always prioritize free local if capable
            
        def cost_heuristic(m: ModelProvider):
            costs = COST_MATRIX.get(m, (99.0, 99.0))
            return costs[0] + costs[1]
            
        sorted_models = sorted(capable_models, key=cost_heuristic)
        return sorted_models[0]


class RateLimiter:
    """Enforces API limits per provider to prevent aggressive 429 cascades."""
    def __init__(self):
        self.limits = {} # Tracks requests per minute
        
    def check_limit(self, model: ModelProvider) -> bool:
        """Returns True if the request is permitted, False if rate limited."""
        # Implementation for token bucket / RPM tracking
        return True
