import time
import logging
from typing import Dict, Any

logger = logging.getLogger("AIFabric.Health")
logger.setLevel(logging.INFO)

class HealthMonitor:
    def __init__(self):
        # Initial health state for all models
        self.state: Dict[str, Dict[str, Any]] = {
            "gemini-2.5-flash": {"provider": "Google", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gemini-2.5-pro": {"provider": "Google", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gemini-deep-think": {"provider": "Google", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gemini-vision": {"provider": "Google", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gpt-5.5": {"provider": "OpenAI", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gpt-5.5-mini": {"provider": "OpenAI", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gpt-5.5-reasoning": {"provider": "OpenAI", "status": "healthy", "latency_ms": 0, "errors": 0},
            "gpt-vision": {"provider": "OpenAI", "status": "healthy", "latency_ms": 0, "errors": 0},
            "claude-sonnet": {"provider": "Anthropic", "status": "healthy", "latency_ms": 0, "errors": 0},
            "claude-opus": {"provider": "Anthropic", "status": "healthy", "latency_ms": 0, "errors": 0},
            "claude-thinking": {"provider": "Anthropic", "status": "healthy", "latency_ms": 0, "errors": 0},
            "mistral-large": {"provider": "Mistral", "status": "healthy", "latency_ms": 0, "errors": 0},
            "mistral-ocr": {"provider": "Mistral", "status": "healthy", "latency_ms": 0, "errors": 0},
            "deepseek-chat": {"provider": "DeepSeek", "status": "healthy", "latency_ms": 0, "errors": 0},
            "deepseek-coder": {"provider": "DeepSeek", "status": "healthy", "latency_ms": 0, "errors": 0},
            "vllm-nemesis": {"provider": "Local", "status": "ready", "latency_ms": 0, "errors": 0},
        }
        
        # Metrics for dashboard
        self.metrics = {
            "requests_sec": 0,
            "avg_latency": 0,
            "fallback_events": 0,
            "active_streams": 0,
            "reasoning_jobs": 0,
            "vision_jobs": 0,
            "queued_tasks": 0,
            "model_distribution": {
                "Gemini Flash": 0,
                "Gemini Pro": 0,
                "Gemini Deep Think": 0,
                "GPT-5.5": 0,
                "Claude": 0,
                "DeepSeek": 0,
                "Local vLLM": 0
            }
        }
        self._request_timestamps = []

    def record_request(self, model: str, latency_ms: int, success: bool, task_type: str = "general"):
        if model in self.state:
            # Update EMA latency
            prev_latency = self.state[model]["latency_ms"]
            self.state[model]["latency_ms"] = int(0.2 * latency_ms + 0.8 * prev_latency) if prev_latency > 0 else latency_ms
            
            if not success:
                self.state[model]["errors"] += 1
                if self.state[model]["errors"] > 3:
                    self.state[model]["status"] = "degraded"
                if self.state[model]["errors"] > 10:
                    self.state[model]["status"] = "offline"
            else:
                self.state[model]["errors"] = max(0, self.state[model]["errors"] - 1)
                if self.state[model]["errors"] == 0:
                    self.state[model]["status"] = "healthy"
            
            # Update distribution mapping
            if "gemini" in model and "flash" in model: self.metrics["model_distribution"]["Gemini Flash"] += 1
            elif "gemini" in model and "pro" in model: self.metrics["model_distribution"]["Gemini Pro"] += 1
            elif "deep-think" in model: self.metrics["model_distribution"]["Gemini Deep Think"] += 1
            elif "gpt" in model: self.metrics["model_distribution"]["GPT-5.5"] += 1
            elif "claude" in model: self.metrics["model_distribution"]["Claude"] += 1
            elif "deepseek" in model: self.metrics["model_distribution"]["DeepSeek"] += 1
            elif "vllm" in model: self.metrics["model_distribution"]["Local vLLM"] += 1
            
            if task_type == "reasoning": self.metrics["reasoning_jobs"] += 1
            if task_type == "vision": self.metrics["vision_jobs"] += 1

        # Track TPS
        now = time.time()
        self._request_timestamps.append(now)
        # Keep only last 10 seconds
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 10]
        self.metrics["requests_sec"] = len(self._request_timestamps) / 10.0

        # Update global avg latency
        all_lats = [s["latency_ms"] for s in self.state.values() if s["latency_ms"] > 0]
        if all_lats:
            self.metrics["avg_latency"] = sum(all_lats) // len(all_lats)

    def record_fallback(self):
        self.metrics["fallback_events"] += 1

    def is_healthy(self, model: str) -> bool:
        if model not in self.state:
            return False
        return self.state[model]["status"] in ["healthy", "ready"]

    def get_dashboard_data(self) -> Dict[str, Any]:
        # Compute health scores by provider
        providers = {"Google": [], "OpenAI": [], "Anthropic": [], "Mistral": [], "DeepSeek": [], "Local": []}
        for m, data in self.state.items():
            if data["provider"] in providers:
                providers[data["provider"]].append(100.0 if data["status"] in ["healthy", "ready"] else (50.0 if data["status"] == "degraded" else 0.0))
        
        health_scores = {}
        for p, scores in providers.items():
            if scores:
                health_scores[p] = round(sum(scores) / len(scores), 1)
            else:
                health_scores[p] = 100.0

        # Normalize distribution percentages
        total_dist = sum(self.metrics["model_distribution"].values())
        dist_pct = {}
        for k, v in self.metrics["model_distribution"].items():
            dist_pct[k] = round((v / total_dist * 100), 1) if total_dist > 0 else 0.0

        return {
            "fabric": self.state,
            "metrics": self.metrics,
            "distribution": dist_pct,
            "health_scores": health_scores
        }

health_monitor = HealthMonitor()
