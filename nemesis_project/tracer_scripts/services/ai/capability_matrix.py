"""
NEMESIS AI FABRIC v3.1 Enterprise
Capability Matrix & Routing Rules
Defines global models, tasks, and optimal fallback chains based on task requirements.
"""

from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("AIFabric.CapabilityMatrix")

class ModelProvider(str, Enum):
    # Google
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_PRO = "gemini-2.5-pro"
    GEMINI_DEEP_THINK = "gemini-deep-think"
    GEMINI_VISION = "gemini-vision"
    GEMINI_EMBEDDINGS = "gemini-embeddings"
    # OpenAI
    GPT_5_5 = "gpt-5.5"
    GPT_5_5_MINI = "gpt-5.5-mini"
    GPT_5_5_REASONING = "gpt-5.5-reasoning"
    GPT_VISION = "gpt-vision"
    # Anthropic
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_OPUS = "claude-opus"
    CLAUDE_THINKING = "claude-thinking"
    CLAUDE_HAIKU = "claude-haiku"
    # DeepSeek
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_REASONER = "deepseek-reasoner"
    DEEPSEEK_CODER = "deepseek-coder"
    # Mistral
    MISTRAL_LARGE = "mistral-large"
    MISTRAL_OCR = "mistral-ocr"
    CODESTRAL = "codestral"
    # Local
    LOCAL_VLLM = "local-vllm"


class AITask(str, Enum):
    BLOCKCHAIN_DECODER = "blockchain_decoder"
    GRAPH_REASONING = "graph_reasoning"
    ENTITY_RESOLUTION = "entity_resolution"
    OCR = "ocr"
    VISION_ANALYSIS = "vision_analysis"
    REPORT_GENERATION = "report_generation"
    CODE_GENERATION = "code_generation"
    JSON_EXTRACTION = "json_extraction"
    TIMELINE_ANALYSIS = "timeline_analysis"
    AML_NARRATIVE = "aml_narrative"
    GRAPH_LABELS = "graph_labels"
    EMBEDDINGS = "embeddings"
    GENERIC_CHAT = "generic_chat"
    OSINT_MCP_QUERY = "osint_mcp_query"


class CapabilityMatrix:
    """
    Enterprise matrix defining the optimal and fallback routes for specific AI tasks.
    """
    
    _routing_rules: Dict[AITask, List[ModelProvider]] = {
        AITask.BLOCKCHAIN_DECODER: [
            ModelProvider.GEMINI_FLASH, 
            ModelProvider.DEEPSEEK_CHAT, 
            ModelProvider.GPT_5_5_MINI
        ],
        AITask.GRAPH_REASONING: [
            ModelProvider.GEMINI_DEEP_THINK, 
            ModelProvider.GPT_5_5_REASONING, 
            ModelProvider.CLAUDE_THINKING
        ],
        AITask.ENTITY_RESOLUTION: [
            ModelProvider.GEMINI_PRO, 
            ModelProvider.GPT_5_5, 
            ModelProvider.CLAUDE_SONNET
        ],
        AITask.OCR: [
            ModelProvider.GEMINI_VISION, 
            ModelProvider.MISTRAL_OCR, 
            ModelProvider.GPT_VISION
        ],
        AITask.VISION_ANALYSIS: [
            ModelProvider.GEMINI_VISION, 
            ModelProvider.CLAUDE_OPUS, 
            ModelProvider.GPT_VISION
        ],
        AITask.REPORT_GENERATION: [
            ModelProvider.GEMINI_PRO, 
            ModelProvider.GPT_5_5, 
            ModelProvider.CLAUDE_OPUS
        ],
        AITask.CODE_GENERATION: [
            ModelProvider.DEEPSEEK_CODER, 
            ModelProvider.GPT_5_5, 
            ModelProvider.CODESTRAL
        ],
        AITask.JSON_EXTRACTION: [
            ModelProvider.GEMINI_FLASH, 
            ModelProvider.GPT_5_5_MINI, 
            ModelProvider.CLAUDE_HAIKU
        ],
        AITask.OSINT_MCP_QUERY: [
            ModelProvider.GEMINI_PRO, # Best at dynamic tool utilization
            ModelProvider.CLAUDE_OPUS,
            ModelProvider.GPT_5_5
        ],
        AITask.TIMELINE_ANALYSIS: [
            ModelProvider.GEMINI_DEEP_THINK, 
            ModelProvider.GPT_5_5, 
            ModelProvider.CLAUDE_THINKING
        ],
        AITask.AML_NARRATIVE: [
            ModelProvider.GEMINI_PRO, 
            ModelProvider.CLAUDE_SONNET, 
            ModelProvider.GPT_5_5
        ],
        AITask.GRAPH_LABELS: [
            ModelProvider.GEMINI_FLASH_LITE, 
            ModelProvider.GEMINI_FLASH, 
            ModelProvider.DEEPSEEK_CHAT
        ],
        AITask.EMBEDDINGS: [
            ModelProvider.GEMINI_EMBEDDINGS
        ],
        AITask.GENERIC_CHAT: [
            ModelProvider.GEMINI_FLASH,
            ModelProvider.GPT_5_5_MINI,
            ModelProvider.LOCAL_VLLM
        ]
    }

    @classmethod
    def get_routing_chain(cls, task: AITask) -> List[ModelProvider]:
        """Returns the prioritized list of models capable of handling the task."""
        chain = cls._routing_rules.get(task, cls._routing_rules[AITask.GENERIC_CHAT])
        logger.debug(f"Routing chain for {task.value}: {[m.value for m in chain]}")
        return chain

    @classmethod
    def get_model_capabilities(cls, model: ModelProvider) -> Dict[str, bool]:
        """Returns a boolean map of specific capabilities supported by a model."""
        # This would be expanded with actual provider specs
        is_vision = model in [ModelProvider.GEMINI_VISION, ModelProvider.GPT_VISION, ModelProvider.MISTRAL_OCR]
        is_reasoning = model in [ModelProvider.GEMINI_DEEP_THINK, ModelProvider.GPT_5_5_REASONING, ModelProvider.CLAUDE_THINKING, ModelProvider.DEEPSEEK_REASONER]
        
        return {
            "vision": is_vision,
            "reasoning": is_reasoning,
            "stream": True,  # Most modern APIs support streaming
            "json": True,    # Most support strict JSON schema
            "tools": model not in [ModelProvider.LOCAL_VLLM] # Assume local vLLM lacks native tools for now
        }
