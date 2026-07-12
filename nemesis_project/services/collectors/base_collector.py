import os
import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("BitqueryPlugin")

class BaseCollector(ABC):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BITQUERY_API_KEY")
        self.endpoint = "https://graphql.bitquery.io"

    @abstractmethod
    def get_query(self) -> str:
        """Returns the Bitquery GraphQL query string."""
        pass

    @abstractmethod
    def get_variables(self, address: str) -> dict:
        """Returns variables for the GraphQL query."""
        pass

    @abstractmethod
    def parse_response(self, data: dict, address: str) -> list:
        """Parses raw Bitquery response into Nemesis standardized edges."""
        pass

    async def fetch(self, address: str, depth: int) -> list:
        if not self.api_key:
            logger.warning(f"No BITQUERY_API_KEY. {self.__class__.__name__} disabled.")
            return []
            
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
        payload = {
            "query": self.get_query(),
            "variables": self.get_variables(address)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_response(data, address)
                    else:
                        logger.error(f"Bitquery Error {response.status}: {await response.text()}")
        except Exception as e:
            logger.error(f"{self.__class__.__name__} fetch failed for {address}: {e}")
            
        return []
