import os
import requests
import json
import logging
import random
import time
from typing import Dict, Any, List, Optional
from requests.exceptions import RequestException

logger = logging.getLogger("AIRouter")
logger.setLevel(logging.INFO)

class AIRouter:
    """
    NEMESIS AI Router with Fallback & Rotation Logic
    Hierarchy:
    1. Gemini 2.5 Flash (Primary - Fast)
    2. Gemini 2.5/3.1 Pro (Fallback 1 - Deep Reasoning)
    3. OpenAI GPT-5.5 (Fallback 2)
    4. DeepSeek (Fallback 3)
    5. Mistral Large (Fallback 4)
    6. Claude 3.5 (Fallback 5)
    7. NEMESIS vLLM (Local / Secure Fallback)
    """

    def __init__(self):
        # API Keys matrix
        self.gemini_keys = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.mistral_key = os.getenv("MISTRAL_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.vllm_endpoint = os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1") # Local NEMESIS LLM
        
        self.current_gemini_key_index = 0

    def _get_next_gemini_key(self) -> str:
        if not self.gemini_keys:
            return ""
        key = self.gemini_keys[self.current_gemini_key_index]
        self.current_gemini_key_index = (self.current_gemini_key_index + 1) % len(self.gemini_keys)
        return key

    def generate(self, prompt: str, system_context: str = "", role: str = "assistant") -> str:
        """
        Executes generation across the fallback hierarchy.
        Returns the text response.
        """
        
        full_prompt = f"System Context: {system_context}\n\nUser Request: {prompt}" if system_context else prompt

        # 1. Gemini 2.5 Flash (Primary)
        try:
            logger.info("Attempting generation via Gemini 2.5 Flash")
            return self._call_gemini(full_prompt, model="gemini-2.5-flash")
        except Exception as e:
            logger.warning(f"Gemini 2.5 Flash failed: {e}. Falling back to Gemini Pro.")

        # 2. Gemini 3.1/2.5 Pro (Fallback 1)
        try:
            logger.info("Attempting generation via Gemini Pro")
            return self._call_gemini(full_prompt, model="gemini-pro")
        except Exception as e:
            logger.warning(f"Gemini Pro failed: {e}. Falling back to OpenAI.")

        # 3. OpenAI GPT-5.5 (Fallback 2)
        try:
            logger.info("Attempting generation via OpenAI")
            return self._call_openai(full_prompt)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}. Falling back to DeepSeek.")

        # 4. DeepSeek (Fallback 3)
        try:
            logger.info("Attempting generation via DeepSeek")
            return self._call_deepseek(full_prompt)
        except Exception as e:
            logger.warning(f"DeepSeek failed: {e}. Falling back to Mistral.")

        # 5. Mistral (Fallback 4)
        try:
            logger.info("Attempting generation via Mistral")
            return self._call_mistral(full_prompt)
        except Exception as e:
            logger.warning(f"Mistral failed: {e}. Falling back to Claude.")

        # 6. Claude (Fallback 5)
        try:
            logger.info("Attempting generation via Claude")
            return self._call_claude(full_prompt)
        except Exception as e:
            logger.warning(f"Claude failed: {e}. Falling back to NEMESIS vLLM.")

        # 7. Local NEMESIS vLLM (Final Fallback)
        try:
            logger.info("Attempting generation via Local NEMESIS vLLM")
            return self._call_vllm(full_prompt)
        except Exception as e:
            logger.error(f"All models in router hierarchy failed. Final error: {e}")
            return "NEMESIS AI ROUTER ERROR: All intelligence nodes offline. Please check API quotas or start Local vLLM."

    def _call_gemini(self, prompt: str, model: str = "gemini-2.5-flash") -> str:
        key = self._get_next_gemini_key()
        if not key:
            raise ValueError("No Gemini keys configured.")
        
        # Adjust URL depending on specific version (using v1beta for newer models)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        if "candidates" in data and data["candidates"]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        raise Exception("Invalid Gemini response format")

    def _call_openai(self, prompt: str) -> str:
        if not self.openai_key:
            raise ValueError("No OpenAI key configured.")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o", # Fallback model if gpt-5.5 not available in endpoint
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_deepseek(self, prompt: str) -> str:
        if not self.deepseek_key:
            raise ValueError("No DeepSeek key configured.")
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_mistral(self, prompt: str) -> str:
        if not self.mistral_key:
            raise ValueError("No Mistral key configured.")
        
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.mistral_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-large-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _call_claude(self, prompt: str) -> str:
        if not self.anthropic_key:
            raise ValueError("No Anthropic key configured.")
            
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def _call_vllm(self, prompt: str) -> str:
        # Calls the Local NEMESIS LLM running via vLLM
        url = f"{self.vllm_endpoint}/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "nemesis-llama-3-8b-instruct", # Placeholder for the local finetune
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

# Global Instance
ai_router = AIRouter()
