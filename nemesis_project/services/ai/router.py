import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from services.ai.health import health_monitor

logger = logging.getLogger("AIFabricRouter")

class AITask(str, Enum):
    BLOCKCHAIN_DECODER = "blockchain_decoder"
    COURT_REPORT = "court_report"
    CHAIN_ATTRIBUTION = "chain_attribution"
    SIGMA_GRAPH = "sigma_graph"
    VISION_OCR = "vision_ocr"
    ENTITY_RESOLUTION = "entity_resolution"
    MASSIVE_LABELING = "massive_labeling"
    JSON_EXTRACTION = "json_extraction"
    CODE_GENERATION = "code_generation"

class ModelProvider(str, Enum):
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_PRO = "gemini-2.5-pro"
    GEMINI_DEEP_THINK = "gemini-deep-think"
    GEMINI_VISION = "gemini-vision"
    GPT_5_5 = "gpt-5.5"
    GPT_5_5_MINI = "gpt-5.5-mini"
    GPT_5_5_REASONING = "gpt-5.5-reasoning"
    GPT_VISION = "gpt-vision"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_THINKING = "claude-thinking"
    DEEPSEEK = "deepseek-chat"
    DEEPSEEK_CODER = "deepseek-coder"
    DEEPSEEK_REASONER = "deepseek-reasoner"
    MISTRAL_LARGE = "mistral-large"
    MISTRAL_OCR = "mistral-ocr"
    PIXTRAL = "pixtral-vision"
    CODESTRAL = "codestral"
    LOCAL_VLLM = "local-vllm"

ROUTING_MATRIX = {
    AITask.BLOCKCHAIN_DECODER: [ModelProvider.GEMINI_FLASH, ModelProvider.DEEPSEEK, ModelProvider.GPT_5_5_MINI],
    AITask.COURT_REPORT: [ModelProvider.GEMINI_PRO, ModelProvider.GPT_5_5, ModelProvider.CLAUDE_OPUS],
    AITask.CHAIN_ATTRIBUTION: [ModelProvider.GEMINI_DEEP_THINK, ModelProvider.GPT_5_5_REASONING, ModelProvider.CLAUDE_THINKING],
    AITask.SIGMA_GRAPH: [ModelProvider.GEMINI_FLASH, ModelProvider.GPT_5_5_MINI],
    AITask.VISION_OCR: [ModelProvider.GEMINI_VISION, ModelProvider.PIXTRAL, ModelProvider.GPT_VISION],
    AITask.ENTITY_RESOLUTION: [ModelProvider.GEMINI_PRO, ModelProvider.GPT_5_5, ModelProvider.DEEPSEEK],
    AITask.MASSIVE_LABELING: [ModelProvider.GEMINI_FLASH_LITE, ModelProvider.GEMINI_FLASH, ModelProvider.DEEPSEEK],
    AITask.JSON_EXTRACTION: [ModelProvider.GEMINI_FLASH, ModelProvider.GPT_5_5_MINI, ModelProvider.DEEPSEEK],
    AITask.CODE_GENERATION: [ModelProvider.DEEPSEEK_CODER, ModelProvider.GPT_5_5, ModelProvider.CODESTRAL],
}

class AIFabricRouter:
    """NEMESIS AI FABRIC v3.1 Enterprise Intelligent Router"""

    def __init__(self):
        self.health = health_monitor

    async def get_best_model(self, task: AITask) -> ModelProvider:
        """Determines the optimal model for a task based on matrix priority and real-time health."""
        fallback_chain = ROUTING_MATRIX.get(task, [ModelProvider.GEMINI_FLASH])
        
        for model in fallback_chain:
            if self.health.is_healthy(model):
                logger.info(f"[AI Router] Selected {model} for task {task}")
                return model
                
        logger.warning(f"[AI Router] All models in chain for {task} failing. Attempting global fallback to Local vLLM.")
        return ModelProvider.LOCAL_VLLM

    async def route_prompt(self, task: AITask, prompt: str, **kwargs) -> str:
        """Executes the prompt against the best available model in the fabric."""
        model = await self.get_best_model(task)
        
        # Here we map the selected model to the actual provider wrapper execution
        self.health.record_request(model)
        try:
            # Placeholder for actual dynamic module execution
            response = await self._execute_provider(model, prompt, **kwargs)
            self.health.record_success(model)
            return response
        except Exception as e:
            logger.error(f"[AI Router] Execution failed for {model}: {str(e)}")
            self.health.record_failure(model)
            # Recursively try again, get_best_model will now skip the failed model
            return await self.route_prompt(task, prompt, **kwargs)

    async def _execute_provider(self, model: ModelProvider, prompt: str, **kwargs) -> str:
        """Dynamically dispatch to the correct provider class based on model Enum."""
        # Simulated dispatcher. In full implementation, this maps to services/ai/providers/
        return f"[Simulated Response from {model.value}] Processed prompt."

router = AIFabricRouter()
