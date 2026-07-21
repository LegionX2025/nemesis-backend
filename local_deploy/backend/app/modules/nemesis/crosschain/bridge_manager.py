# nemesis/crosschain/bridge_manager.py

from typing import List, Dict, Any, Optional
from nemesis.crosschain.interfaces import BridgeAdapter
from nemesis.crosschain.adapters.wormhole import WormholeAdapter
from nemesis.observability.telemetry import logger, tracer

class BridgeManager:
    def __init__(self):
        self.adapters: List[BridgeAdapter] = []
        self._register_adapters()

    def _register_adapters(self):
        self.adapters.append(WormholeAdapter())
        # Other adapters would be registered here (LayerZero, CCIP, etc.)
        logger.info(f"BridgeManager initialized with {len(self.adapters)} adapters.")

    @tracer.start_as_current_span("bridge_manager.analyze_tx")
    async def analyze_crosschain_tx(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for adapter in self.adapters:
            if await adapter.detect_bridge(tx):
                logger.info(f"Detected {adapter.name} interaction in tx {tx.get('hash')}")
                return await adapter.reconstruct_path(tx)
        return None

# Singleton
bridge_manager = BridgeManager()
