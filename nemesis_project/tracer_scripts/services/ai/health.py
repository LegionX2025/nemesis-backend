"""
NEMESIS AI FABRIC v3.1 Enterprise
Health & Telemetry Monitor
Tracks Latency, Error Rates, Tokens, and Quota for each AI Provider.
"""

import time
import logging
from typing import Dict, Any
from tracer_scripts.services.ai.capability_matrix import ModelProvider

logger = logging.getLogger("AIFabric.Health")

class HealthState:
    def __init__(self):
        self.status: str = "healthy"
        self.total_requests: int = 0
        self.failed_requests: int = 0
        self.total_latency_ms: float = 0.0
        self.avg_latency_ms: float = 0.0
        self.error_rate: float = 0.0
        self.last_failed_at: float = 0.0
        self.circuit_open: bool = False

class HealthMonitor:
    def __init__(self):
        self._states: Dict[ModelProvider, HealthState] = {}
        for provider in ModelProvider:
            self._states[provider] = HealthState()
            
        self.CIRCUIT_BREAKER_THRESHOLD = 0.25 # 25% failure rate triggers circuit break
        self.CIRCUIT_BREAKER_TIMEOUT = 60 # wait 60 seconds before retrying a broken circuit

    def is_healthy(self, model: ModelProvider) -> bool:
        """Returns True if the model is ready to receive traffic."""
        state = self._states[model]
        
        if state.circuit_open:
            if time.time() - state.last_failed_at > self.CIRCUIT_BREAKER_TIMEOUT:
                logger.info(f"[AI Health] Attempting circuit reset for {model.value}")
                state.circuit_open = False # Half-open state
                return True
            return False
            
        return state.status == "healthy"

    def record_start(self, model: ModelProvider) -> float:
        """Records the start of a request for latency tracking."""
        return time.time()

    def record_success(self, model: ModelProvider, start_time: float):
        """Records a successful request and updates latency averages."""
        state = self._states[model]
        latency = (time.time() - start_time) * 1000
        
        state.total_requests += 1
        state.total_latency_ms += latency
        state.avg_latency_ms = state.total_latency_ms / state.total_requests
        
        # Self-healing if circuit was open
        if state.circuit_open or state.status == "failing":
            state.circuit_open = False
            state.status = "healthy"
            logger.info(f"[AI Health] {model.value} recovered and is healthy.")
            
        self._recalculate(model)

    def record_failure(self, model: ModelProvider):
        """Records a failed request and evaluates circuit breaker conditions."""
        state = self._states[model]
        state.total_requests += 1
        state.failed_requests += 1
        state.last_failed_at = time.time()
        
        self._recalculate(model)
        
        if state.error_rate >= self.CIRCUIT_BREAKER_THRESHOLD:
            state.status = "failing"
            state.circuit_open = True
            logger.error(f"[AI Health] CIRCUIT OPENED for {model.value} (Error Rate: {state.error_rate:.2f})")

    def _recalculate(self, model: ModelProvider):
        state = self._states[model]
        if state.total_requests > 0:
            state.error_rate = state.failed_requests / state.total_requests

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Generates the metrics payload required by the NEMESIS Admin Dashboard."""
        provider_stats = {}
        total_reqs = 0
        total_fails = 0
        
        for p, s in self._states.items():
            provider_stats[p.value] = {
                "status": s.status,
                "latency_ms": int(s.avg_latency_ms),
                "error_rate": s.error_rate,
                "total_requests": s.total_requests
            }
            total_reqs += s.total_requests
            total_fails += s.failed_requests
            
        return {
            "providers": provider_stats,
            "global_metrics": {
                "requests_per_sec": total_reqs / 60.0, # Approximate RPM window
                "avg_latency": sum(s.avg_latency_ms for s in self._states.values()) / len(self._states),
                "fallback_events": total_fails
            }
        }

# Global singleton
fabric_health = HealthMonitor()
