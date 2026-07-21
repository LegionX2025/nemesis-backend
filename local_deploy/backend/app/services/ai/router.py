import os
import requests
import json
import logging
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from services.ai.health import health_monitor

logger = logging.getLogger("AIFabric.Router")
logger.setLevel(logging.INFO)

class TaskType(Enum):
    BLOCKCHAIN_DECODER = "blockchain_decoder"
    COURT_REPORT = "court_report"
    CHAIN_ATTRIBUTION = "chain_attribution"
    SIGMA_GRAPH = "sigma_graph"
    VISION = "vision"
    OCR = "ocr"
    ENTITY_RESOLUTION = "entity_resolution"
    MASSIVE_LABELING = "massive_labeling"
    GENERAL_CHAT = "general_chat"
    AUTO_FIX = "auto_fix"
    CODE_GENERATION = "code_generation"
    SYSTEM_MONITOR = "system_monitor"

# Capability Matrix defining Primary, Secondary, Fallback per task
CAPABILITY_MATRIX = {
    TaskType.BLOCKCHAIN_DECODER: ["gemini-2.5-flash", "deepseek-chat", "gpt-5.5-mini"],
    TaskType.COURT_REPORT: ["gemini-2.5-pro", "gpt-5.5", "claude-opus"],
    TaskType.CHAIN_ATTRIBUTION: ["gemini-deep-think", "gpt-5.5-reasoning", "claude-thinking"],
    TaskType.SIGMA_GRAPH: ["gemini-2.5-flash", "gpt-5.5-mini"],
    TaskType.VISION: ["gemini-vision", "gpt-vision", "pixtral"],
    TaskType.OCR: ["gemini-vision", "mistral-ocr", "gpt-vision"],
    ENTITY_RESOLUTION: ["gemini-3.1-pro", "gemini-2.5-pro", "gpt-5.5", "deepseek-chat"],
    MASSIVE_LABELING: ["gemini-3.0-flash", "gemini-2.5-flash", "deepseek-chat"],
    GENERAL_CHAT: ["gemini-3.0-flash", "gemini-2.5-flash", "gpt-5.5", "claude-sonnet", "vllm-nemesis"],
    TaskType.AUTO_FIX: ["gemini-3.1-pro-extended", "gemini-3.0-pro"],
    TaskType.CODE_GENERATION: ["gemini-3.1-pro-extended", "gemini-3.0-pro"],
    TaskType.SYSTEM_MONITOR: ["gemini-3.0-flash", "gemini-3.1-flash"]
}

class AIFabricRouter:
    """
    NEMESIS AI FABRIC v3.1 Enterprise
    Intelligent routing layer that determines the optimal model based on the task,
    monitors health, and fails over resiliently.
    """

    def __init__(self):
        # API Keys matrix
        self.gemini_keys = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.mistral_key = os.getenv("MISTRAL_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.vllm_endpoint = os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1")
        
        self.current_gemini_key_index = 0

    def _get_next_gemini_key(self) -> str:
        if not self.gemini_keys: return ""
        key = self.gemini_keys[self.current_gemini_key_index]
        self.current_gemini_key_index = (self.current_gemini_key_index + 1) % len(self.gemini_keys)
        return key

    def get_optimal_model_sequence(self, task_type: TaskType) -> List[str]:
        return CAPABILITY_MATRIX.get(task_type, CAPABILITY_MATRIX[TaskType.GENERAL_CHAT])

    def generate(self, prompt: str, system_context: str = "", task_type: TaskType = TaskType.GENERAL_CHAT) -> str:
        sequence = self.get_optimal_model_sequence(task_type)
        full_prompt = f"System Context: {system_context}\n\nUser Request: {prompt}" if system_context else prompt

        for model in sequence:
            if not health_monitor.is_healthy(model):
                logger.warning(f"Skipping {model} due to health status: {health_monitor.state.get(model, {}).get('status', 'unknown')}")
                continue
                
            logger.info(f"Routing task {task_type.name} to {model}")
            start_time = time.time()
            try:
                # Dispatch to specific provider logic
                reply = self._dispatch(model, full_prompt)
                latency = int((time.time() - start_time) * 1000)
                
                # Record success
                task_cat = "reasoning" if "think" in model or "reasoning" in model else ("vision" if "vision" in model or "ocr" in model else "general")
                health_monitor.record_request(model, latency, True, task_type=task_cat)
                return reply
                
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}. Failing over.")
                latency = int((time.time() - start_time) * 1000)
                health_monitor.record_request(model, latency, False)
                health_monitor.record_fallback()
                
        # Final desperate fallback to Local vLLM if it wasn't in the sequence
        if "vllm-nemesis" not in sequence and health_monitor.is_healthy("vllm-nemesis"):
            logger.warning("All models in sequence failed. Desperate fallback to Local vLLM.")
            try:
                start_time = time.time()
                reply = self._call_vllm(full_prompt)
                health_monitor.record_request("vllm-nemesis", int((time.time() - start_time) * 1000), True)
                return reply
            except Exception as e:
                pass
                
        raise Exception("NEMESIS AI FABRIC ERROR: All intelligence nodes offline for this task.")

    def _dispatch(self, model: str, prompt: str) -> str:
        # In a full enterprise structure, these would be in providers/ folder classes.
        # For this execution, we implement the unified REST wrappers here for speed.
        if "gemini" in model:
            # Map logical names to actual google models
            g_model = "gemini-2.5-flash"
            if "3.0" in model:
                g_model = "gemini-3.0-flash"
                if "pro" in model: g_model = "gemini-3.0-pro"
            elif "3.1" in model:
                g_model = "gemini-3.1-flash"
                if "pro" in model: g_model = "gemini-3.1-pro"
                if "extended" in model: g_model = "gemini-3.1-pro-extended"
            else:
                if "pro" in model: g_model = "gemini-pro"
                if "lite" in model: g_model = "gemini-2.5-flash-lite-preview"
                if "think" in model: g_model = "gemini-2.0-pro-exp"
            return self._call_gemini(prompt, g_model)
            
        elif "gpt" in model:
            o_model = "gpt-4o" # Fallback mapping for 5.5
            if "mini" in model: o_model = "gpt-4o-mini"
            if "reasoning" in model: o_model = "o3-mini"
            return self._call_openai(prompt, o_model)
            
        elif "claude" in model:
            c_model = "claude-3-5-sonnet-20241022"
            if "opus" in model: c_model = "claude-3-opus-20240229"
            if "thinking" in model: c_model = "claude-3-5-sonnet-20241022" # + thinking block
            return self._call_claude(prompt, c_model)
            
        elif "deepseek" in model:
            d_model = "deepseek-chat"
            if "coder" in model: d_model = "deepseek-coder"
            return self._call_deepseek(prompt, d_model)
            
        elif "mistral" in model or "pixtral" in model:
            m_model = "mistral-large-latest"
            if "pixtral" in model: m_model = "pixtral-large-latest"
            return self._call_mistral(prompt, m_model)
            
        elif "vllm" in model:
            return self._call_vllm(prompt)
            
        raise ValueError(f"Unknown model identifier: {model}")

    def _call_gemini(self, prompt: str, model: str) -> str:
        key = self._get_next_gemini_key()
        if not key: raise ValueError("No Gemini keys configured.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096}}
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if "candidates" in data and data["candidates"]: return data["candidates"][0]["content"]["parts"][0]["text"]
        raise Exception("Invalid Gemini response format")

    def _call_openai(self, prompt: str, model: str) -> str:
        if not self.openai_key: raise ValueError("No OpenAI key configured.")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_deepseek(self, prompt: str, model: str) -> str:
        if not self.deepseek_key: raise ValueError("No DeepSeek key configured.")
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.deepseek_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_mistral(self, prompt: str, model: str) -> str:
        if not self.mistral_key: raise ValueError("No Mistral key configured.")
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.mistral_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_claude(self, prompt: str, model: str) -> str:
        if not self.anthropic_key: raise ValueError("No Anthropic key configured.")
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": self.anthropic_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _call_vllm(self, prompt: str) -> str:
        url = f"{self.vllm_endpoint}/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {"model": "nemesis-llama-3-8b-instruct", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

# Global Instance
ai_fabric_router = AIFabricRouter()
