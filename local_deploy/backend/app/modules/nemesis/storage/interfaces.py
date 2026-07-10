# nemesis/storage/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class GraphStore(ABC):
    @abstractmethod
    async def connect(self):
        pass
        
    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def add_node(self, node_id: str, attributes: Dict[str, Any]):
        pass

    @abstractmethod
    async def add_edge(self, from_id: str, to_id: str, edge_type: str, attributes: Dict[str, Any]):
        pass
        
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        pass

class DocumentStore(ABC):
    @abstractmethod
    async def connect(self):
        pass
        
    @abstractmethod
    async def close(self):
        pass
        
    @abstractmethod
    async def save_trace(self, trace_id: str, data: Dict[str, Any]):
        pass

    @abstractmethod
    async def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        pass

class CacheStore(ABC):
    @abstractmethod
    async def connect(self):
        pass
        
    @abstractmethod
    async def close(self):
        pass
        
    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int = 3600):
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass
