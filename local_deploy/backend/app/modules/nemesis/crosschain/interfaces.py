# nemesis/crosschain/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AssetLineage(BaseModel):
    asset_id: str
    origin_chain: str
    wrapped_chain: str
    mint_tx: Optional[str] = None
    burn_tx: Optional[str] = None
    bridge_used: Optional[str] = None
    holder_history: list = Field(default_factory=list)
    swap_history: list = Field(default_factory=list)
    confidence: float = 1.0

class BridgeMessage(BaseModel):
    source_chain: str
    destination_chain: str
    sender: str
    recipient: str
    payload: str
    sequence: int
    raw_event: Dict[str, Any]

class BridgeAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def detect_bridge(self, tx: Dict[str, Any]) -> bool:
        """Detect if this transaction is interacting with this specific bridge."""
        pass

    @abstractmethod
    async def extract_message(self, tx: Dict[str, Any]) -> Optional[BridgeMessage]:
        """Extract the cross-chain message from the transaction logs/events."""
        pass

    @abstractmethod
    async def locate_destination(self, message: BridgeMessage) -> Optional[str]:
        """Find the corresponding transaction on the destination chain."""
        pass

    @abstractmethod
    async def verify_proof(self, message: BridgeMessage) -> float:
        """Verify the cryptographic proof of the bridge message. Returns a confidence score."""
        pass

    @abstractmethod
    async def reconstruct_path(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fully reconstruct the cross-chain hop."""
        pass
