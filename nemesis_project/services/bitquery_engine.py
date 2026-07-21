import os
import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("BitqueryEngine")

class BitqueryGraphQLClient:
    def __init__(self):
        self.v2_token = os.getenv("BITQUERY_V2_TOKEN")
        self.v1_token = os.getenv("BITQUERY_V1_TOKEN")
        self.endpoint_v2 = "https://streaming.bitquery.io/graphql"
        
    async def _execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a raw GraphQL query against Bitquery V2"""
        if not self.v2_token:
            logger.warning("BITQUERY_V2_TOKEN is missing. Returning empty.")
            return {}
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.v2_token}"
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint_v2, headers=headers, json=payload, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", {})
                    else:
                        error_text = await resp.text()
                        logger.error(f"Bitquery API Error ({resp.status}): {error_text}")
                        return {}
        except Exception as e:
            logger.error(f"Bitquery Execution Failed: {str(e)}")
            return {}

    async def get_address_transactions(self, address: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Fetch transactions for a specific address with strict pagination."""
        query = """
        query getTransactions($address: String!, $limit: Int!, $offset: Int!) {
          EVM(dataset: combined, network: eth) {
            Transactions(
              where: {Block: {Date: {since: "2023-01-01"}}, any: [{Transaction: {From: {is: $address}}}, {Transaction: {To: {is: $address}}}]}
              limit: {count: $limit, offset: $offset}
              orderBy: {descending: Block_Time}
            ) {
              Transaction {
                Hash
                From
                To
                Value
              }
              Block {
                Time
              }
            }
          }
        }
        """
        variables = {
            "address": address,
            "limit": limit,
            "offset": offset
        }
        result = await self._execute_query(query, variables)
        try:
            return result["EVM"]["Transactions"]
        except KeyError:
            return []

    async def get_dex_trades(self, token_address: str, limit: int = 50) -> List[Dict]:
        """Fetch DEX trades for a specific token with strict limits."""
        query = """
        query getDexTrades($token: String!, $limit: Int!) {
          EVM(dataset: combined, network: eth) {
            DEXTrades(
              where: {Trade: {Buy: {Currency: {SmartContract: {is: $token}}}}}
              limit: {count: $limit}
              orderBy: {descending: Block_Time}
            ) {
              Trade {
                Buy {
                  Amount
                  Buyer
                  Currency {
                    Symbol
                  }
                }
                Sell {
                  Amount
                  Seller
                  Currency {
                    Symbol
                  }
                }
              }
              Block {
                Time
              }
            }
          }
        }
        """
        variables = {"token": token_address, "limit": limit}
        result = await self._execute_query(query, variables)
        try:
            return result["EVM"]["DEXTrades"]
        except KeyError:
            return []

class BitqueryWebhookReceiver:
    """
    Acts as a bridge to consume Bitquery Kafka/Streaming events at the Edge.
    Instead of a native Kafka Consumer loop (unsupported in Cloudflare Workers),
    this receives HTTP Webhooks directly from Bitquery Cloud.
    """
    @staticmethod
    async def process_event(payload: dict):
        """Processes live streamed transaction events"""
        event_type = payload.get("type", "unknown")
        logger.info(f"[Bitquery Streaming] Processing webhook event: {event_type}")
        # Routing to graph database or UI hydration will occur here
        return True

# Singleton Instances
bitquery_client = BitqueryGraphQLClient()
bitquery_receiver = BitqueryWebhookReceiver()
