"""
NEMESIS AI FABRIC v3.1 Enterprise
Task Classifier
Dynamically classifies incoming text/prompts into specific AITask categories.
"""

import logging
import re
from typing import Optional
from tracer_scripts.services.ai.capability_matrix import AITask

logger = logging.getLogger("AIFabric.Classifier")

class TaskClassifier:
    """
    Classifies an incoming payload to determine the optimal AI Task routing.
    In a full production scenario, this could use a lightweight ML model 
    (e.g., FastText or a small local transformer) to categorize intents.
    For this implementation, we use advanced heuristic regex matching.
    """
    
    _rules = {
        AITask.BLOCKCHAIN_DECODER: [
            r"\b(0x[a-fA-F0-9]{40})\b",
            r"\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b",
            r"\b(txn|hash|contract|decode)\b"
        ],
        AITask.CODE_GENERATION: [
            r"\b(write a python script|generate code|implement function|refactor)\b",
            r"\b(def |class |import |function\() "
        ],
        AITask.JSON_EXTRACTION: [
            r"\b(extract to json|parse json|return json)\b",
            r"```json"
        ],
        AITask.REPORT_GENERATION: [
            r"\b(generate report|write dossier|summarize findings|executive summary)\b"
        ],
        AITask.GRAPH_REASONING: [
            r"\b(graph analysis|paths between|shortest path|centrality|analyze network)\b"
        ],
        AITask.AML_NARRATIVE: [
            r"\b(money laundering|sanctions evasion|aml|kyc|suspicious activity report)\b"
        ]
    }

    @classmethod
    def classify_prompt(cls, prompt: str) -> AITask:
        """
        Analyzes the prompt text to determine the best AITask category.
        Falls back to GENERIC_CHAT if no specific patterns match.
        """
        prompt_lower = prompt.lower()
        
        # Heuristic matching based on predefined rules
        for task, patterns in cls._rules.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    logger.debug(f"Prompt classified as {task.value} based on pattern match.")
                    return task
                    
        # Default fallback
        logger.debug("Prompt classified as GENERIC_CHAT (default fallback).")
        return AITask.GENERIC_CHAT
