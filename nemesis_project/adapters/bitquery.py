import os
import aiohttp
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger("OmniChainEngine.Bitquery")

class BitqueryAdapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BITQUERY_V2_TOKEN") or os.getenv("BITQUERY_API_TOKEN")
        self.url = "https://streaming.bitquery.io/graphql"
        self.headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {self.api_key}"
        } if self.api_key else {}

    def _get_network_name(self, chain: str) -> str:
        """Map Nemesis chain names to Bitquery V2 network dataset names."""
        chain = chain.upper()
        mapping = {
            "ETHEREUM": "eth",
            "BSC": "bsc",
            "POLYGON": "matic",
            "ARBITRUM": "arbitrum",
            "OPTIMISM": "optimism",
            "BASE": "base",
            "AVALANCHE": "avalanche",
            "TRON": "tron",
            "SOLANA": "solana",
            "BITCOIN": "bitcoin"
        }
        return mapping.get(chain)

    async def get_transactions(self, session: aiohttp.ClientSession, address: str, chain: str, limit: int = 50):
        if not self.api_key:
            logger.warning("BitqueryAdapter: No API key configured.")
            return []
            
        network = self._get_network_name(chain)
        if not network:
            logger.warning(f"BitqueryAdapter: Unsupported network for chain {chain}")
            return []

        results = []
        
        # Determine GraphQL schema based on architecture (EVM vs Solana vs UTXO)
        if chain in ["ETHEREUM", "BSC", "POLYGON", "ARBITRUM", "OPTIMISM", "BASE", "AVALANCHE", "TRON"]:
            query = """
            query ($network: evm_network, $address: String, $limit: Int) {
              EVM(network: $network, dataset: combined) {
                Transfers(
                  where: {any: [{Transfer: {Sender: {eq: $address}}}, {Transfer: {Receiver: {eq: $address}}}]}
                  limit: {count: $limit}
                  orderBy: {descending: Block_Time}
                ) {
                  Transaction { Hash }
                  Transfer { 
                    Sender 
                    Receiver 
                    Amount 
                    Currency { Symbol SmartContract }
                  }
                  Block { Time }
                }
              }
            }
            """
            variables = {"network": network, "address": address.lower(), "limit": limit}
            try:
                async with session.post(self.url, json={"query": query, "variables": variables}, headers=self.headers, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        transfers = data.get("data", {}).get("EVM", {}).get("Transfers", [])
                        for t in transfers:
                            try:
                                ts_str = t.get("Block", {}).get("Time", "")
                                ts = str(int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())) if ts_str else str(int(datetime.now(timezone.utc).timestamp()))
                            except: ts = str(int(datetime.now(timezone.utc).timestamp()))
                            
                            results.append({
                                "hash": t.get("Transaction", {}).get("Hash"),
                                "from": t.get("Transfer", {}).get("Sender"),
                                "to": t.get("Transfer", {}).get("Receiver"),
                                "value": str(t.get("Transfer", {}).get("Amount", 0)),
                                "timestamp": ts,
                                "contractAddress": t.get("Transfer", {}).get("Currency", {}).get("SmartContract", ""),
                                "tokenSymbol": t.get("Transfer", {}).get("Currency", {}).get("Symbol", "")
                            })
            except Exception as e:
                logger.error(f"BitqueryAdapter EVM fetch error: {e}")
                
        elif chain == "SOLANA":
            query = """
            query ($address: String, $limit: Int) {
              Solana {
                Transfers(
                  where: {any: [{Transfer: {Sender: {Address: {is: $address}}}}, {Transfer: {Receiver: {Address: {is: $address}}}}]}
                  limit: {count: $limit}
                  orderBy: {descending: Block_Time}
                ) {
                  Transaction { Signatures }
                  Transfer {
                    Sender { Address }
                    Receiver { Address }
                    Amount
                    Currency { Symbol MintAddress }
                  }
                  Block { Time }
                }
              }
            }
            """
            variables = {"address": address, "limit": limit}
            try:
                async with session.post(self.url, json={"query": query, "variables": variables}, headers=self.headers, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        transfers = data.get("data", {}).get("Solana", {}).get("Transfers", [])
                        for t in transfers:
                            try:
                                ts_str = t.get("Block", {}).get("Time", "")
                                ts = str(int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())) if ts_str else str(int(datetime.now(timezone.utc).timestamp()))
                            except: ts = str(int(datetime.now(timezone.utc).timestamp()))
                            
                            sigs = t.get("Transaction", {}).get("Signatures", [])
                            tx_hash = sigs[0] if sigs else ""
                            
                            results.append({
                                "hash": tx_hash,
                                "from": t.get("Transfer", {}).get("Sender", {}).get("Address"),
                                "to": t.get("Transfer", {}).get("Receiver", {}).get("Address"),
                                "value": str(t.get("Transfer", {}).get("Amount", 0)),
                                "timestamp": ts,
                                "contractAddress": t.get("Transfer", {}).get("Currency", {}).get("MintAddress", ""),
                                "tokenSymbol": t.get("Transfer", {}).get("Currency", {}).get("Symbol", "")
                            })
            except Exception as e:
                logger.error(f"BitqueryAdapter Solana fetch error: {e}")
                
        elif chain == "BITCOIN":
            query = """
            query ($address: String, $limit: Int) {
              Bitcoin {
                Inputs(
                  where: {Input: {Address: {is: $address}}}
                  limit: {count: $limit}
                  orderBy: {descending: Block_Time}
                ) {
                  Transaction { Hash }
                  Input { Address Value }
                  Block { Time }
                }
                Outputs(
                  where: {Output: {Address: {is: $address}}}
                  limit: {count: $limit}
                  orderBy: {descending: Block_Time}
                ) {
                  Transaction { Hash }
                  Output { Address Value }
                  Block { Time }
                }
              }
            }
            """
            variables = {"address": address, "limit": limit}
            try:
                async with session.post(self.url, json={"query": query, "variables": variables}, headers=self.headers, timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        inputs = data.get("data", {}).get("Bitcoin", {}).get("Inputs", [])
                        outputs = data.get("data", {}).get("Bitcoin", {}).get("Outputs", [])
                        
                        # Process Inputs (Sent)
                        for i in inputs:
                            try:
                                ts_str = i.get("Block", {}).get("Time", "")
                                ts = str(int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())) if ts_str else str(int(datetime.now(timezone.utc).timestamp()))
                            except: ts = str(int(datetime.now(timezone.utc).timestamp()))
                            results.append({
                                "hash": i.get("Transaction", {}).get("Hash"),
                                "from": i.get("Input", {}).get("Address"),
                                "to": "", # Unknown from Input alone
                                "value": str(i.get("Input", {}).get("Value", 0)),
                                "timestamp": ts
                            })
                            
                        # Process Outputs (Received)
                        for o in outputs:
                            try:
                                ts_str = o.get("Block", {}).get("Time", "")
                                ts = str(int(datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp())) if ts_str else str(int(datetime.now(timezone.utc).timestamp()))
                            except: ts = str(int(datetime.now(timezone.utc).timestamp()))
                            results.append({
                                "hash": o.get("Transaction", {}).get("Hash"),
                                "from": "", # Unknown from Output alone
                                "to": o.get("Output", {}).get("Address"),
                                "value": str(o.get("Output", {}).get("Value", 0)),
                                "timestamp": ts
                            })
            except Exception as e:
                logger.error(f"BitqueryAdapter Bitcoin fetch error: {e}")

        return results
