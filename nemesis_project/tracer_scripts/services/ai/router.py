"""
NEMESIS AI FABRIC v3.1 Enterprise
Unified AI Router
Orchestrates capability matching, health tracking, cost optimization, and fallback.
"""

import logging
from typing import Optional, Dict, Any
from tracer_scripts.services.ai.capability_matrix import CapabilityMatrix, AITask, ModelProvider
from tracer_scripts.services.ai.classifier import TaskClassifier
from tracer_scripts.services.ai.health import fabric_health
from tracer_scripts.services.ai.cost_optimizer import CostOptimizer, RateLimiter

logger = logging.getLogger("AIFabric.Router")

class AIFabricRouter:
    """The central nervous system of the NEMESIS AI Fabric."""
    
    def __init__(self):
        self.health = fabric_health
        self.rate_limiter = RateLimiter()

    async def _select_best_model(self, task: AITask) -> ModelProvider:
        """Determines the absolute best model based on task, health, and limits."""
        # 1. Get the primary and fallback chain for the specific task
        routing_chain = CapabilityMatrix.get_routing_chain(task)
        
        capable_models = []
        for model in routing_chain:
            # 2. Check real-time health and rate limits
            if self.health.is_healthy(model) and self.rate_limiter.check_limit(model):
                capable_models.append(model)
                
        if not capable_models:
            logger.critical(f"[AI Router] FATAL: Entire routing chain failed for {task.value}. Forcing Local vLLM Fallback.")
            return ModelProvider.LOCAL_VLLM
            
        # 3. Optional: Pass through cost optimizer if multiple are viable and healthy
        best_model = capable_models[0] # For now, strict priority mapping
        logger.info(f"[AI Router] Selected {best_model.value} for task {task.value}")
        return best_model

    async def execute_prompt(self, prompt: str, system_instruction: str = "", **kwargs) -> str:
        """
        The main enterprise entrypoint.
        Automatically classifies the prompt, selects the model, and executes.
        """
        # Phase 1: Classification
        task = TaskClassifier.classify_prompt(prompt)
        
        # Phase 2: Route Selection
        model = await self._select_best_model(task)
        
        # Phase 3: Execution & Telemetry
        start_time = self.health.record_start(model)
        try:
            # Call the provider manager (to be implemented)
            response = await self._dispatch_to_provider(model, prompt, system_instruction, **kwargs)
            
            # Telemetry success
            self.health.record_success(model, start_time)
            return response
            
        except Exception as e:
            # Telemetry failure
            self.health.record_failure(model)
            logger.error(f"[AI Router] Execution failed for {model.value}: {str(e)}")
            
            # Phase 4: Recursive Fallback
            logger.info(f"[AI Router] Triggering recursive fallback for {task.value}...")
            return await self.execute_prompt(prompt, system_instruction, **kwargs)

    async def _dispatch_to_provider(self, model: ModelProvider, prompt: str, system_instruction: str, **kwargs) -> str:
        """Dynamically dispatches to the correct AI Stack adapter."""
        from tracer_scripts.services.ai.provider_manager import provider_manager
        
        provider = provider_manager.get_provider(model)
        logger.debug(f"[AI Router] Dispatching to {provider.__class__.__name__} for model {model.value}")
        return await provider.execute(model, prompt, system_instruction, **kwargs)

# Global singleton
fabric_router = AIFabricRouter()
