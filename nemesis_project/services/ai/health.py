import time
import logging
from typing import Dict, Any

logger = logging.getLogger("AIFabricHealth")

class HealthMonitor:
    def __init__(self):
        self.stats = {}
        # Pre-populate some baseline states for the dashboard
        self._initialize_stats()

    def _initialize_stats(self):
        providers = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-deep-think", 
                     "gpt-5.5", "gpt-5.5-mini", "claude-sonnet", "deepseek-chat", "local-vllm"]
        for p in providers:
            self.stats[p] = {
                "status": "healthy",
                "latency_ms": 300,
                "error_rate": 0.0,
                "total_requests": 0,
                "failed_requests": 0
            }

    def is_healthy(self, model: str) -> bool:
        """Returns True if the model is currently healthy and not rate-limited."""
        stat = self.stats.get(model, {})
        return stat.get("status") == "healthy" and stat.get("error_rate", 0.0) < 0.15

    def record_request(self, model: str):
        if model not in self.stats:
            self._initialize_stats() # Fallback
        self.stats[model]["total_requests"] += 1

    def record_success(self, model: str):
        # In a real app, we'd record actual latency here
        self._update_error_rate(model)

    def record_failure(self, model: str):
        if model in self.stats:
            self.stats[model]["failed_requests"] += 1
            self._update_error_rate(model)
            if self.stats[model]["error_rate"] >= 0.15:
                self.stats[model]["status"] = "failing"
                logger.warning(f"[AI Health] {model} marked as FAILING due to high error rate.")

    def _update_error_rate(self, model: str):
        total = self.stats[model]["total_requests"]
        failed = self.stats[model]["failed_requests"]
        if total > 0:
            self.stats[model]["error_rate"] = failed / total

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Formats the stats for the Admin UI."""
        return {
            "providers": self.stats,
            "global_metrics": {
                "requests_per_sec": sum(s["total_requests"] for s in self.stats.values()) / 60.0, # Simulated
                "avg_latency": 382, # Simulated average
                "fallback_events": sum(s["failed_requests"] for s in self.stats.values())
            }
        }

health_monitor = HealthMonitor()
