import logging
from datetime import datetime
from services.collectors.base_collector import BaseCollector

logger = logging.getLogger("BitqueryPlugins")

class TransferCollector(BaseCollector):
    """Fetches ERC20 and Native transfers."""
    
    def get_query(self) -> str:
        return """
        query ($address: String!) {
            ethereum(network: ethereum) {
                transfers(sender: {is: $address}, options: {limit: 50, desc: "block.timestamp.time"}) {
                    transaction { hash }
                    receiver { address annotation }
                    currency { symbol address }
                    amount
                    amount_usd: amount(in: USD)
                    block { timestamp { time(format: "%Y-%m-%dT%H:%M:%SZ") } }
                }
            }
        }
        """

    def get_variables(self, address: str) -> dict:
        return {"address": address}

    def parse_response(self, data: dict, address: str) -> list:
        edges = []
        transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
        for t in transfers:
            to_addr = t.get("receiver", {}).get("address")
            if not to_addr or to_addr.lower() == address.lower(): continue
            
            edges.append({
                "edge_type": "SENT_TO",
                "tx": t.get("transaction", {}).get("hash"),
                "from": address,
                "to": to_addr,
                "amount": t.get("amount", 0),
                "usd_value": t.get("amount_usd", 0),
                "currency": t.get("currency", {}).get("symbol", "ETH"),
                "timestamp": t.get("block", {}).get("timestamp", {}).get("time", datetime.utcnow().isoformat()),
                "receiver_entity": t.get("receiver", {}).get("annotation", "Unknown"),
                "is_terminal": t.get("receiver", {}).get("annotation") is not None
            })
        return edges

class DexCollector(BaseCollector):
    """Fetches DEX Trades (Swaps)."""
    
    def get_query(self) -> str:
        return """
        query ($address: String!) {
            ethereum(network: ethereum) {
                dexTrades(txSender: {is: $address}, options: {limit: 50, desc: "block.timestamp.time"}) {
                    transaction { hash }
                    exchange { fullName }
                    buyCurrency { symbol }
                    buyAmount
                    buyAmountInUSD: buyAmount(in: USD)
                    sellCurrency { symbol }
                    sellAmount
                    block { timestamp { time(format: "%Y-%m-%dT%H:%M:%SZ") } }
                }
            }
        }
        """

    def get_variables(self, address: str) -> dict:
        return {"address": address}

    def parse_response(self, data: dict, address: str) -> list:
        edges = []
        trades = data.get("data", {}).get("ethereum", {}).get("dexTrades", [])
        for t in trades:
            edges.append({
                "edge_type": "SWAPPED_TO",
                "tx": t.get("transaction", {}).get("hash"),
                "from": address,
                "to": "DEX_CONTRACT", # Usually we'd resolve the exact DEX router
                "amount": t.get("buyAmount", 0),
                "usd_value": t.get("buyAmountInUSD", 0),
                "currency": t.get("buyCurrency", {}).get("symbol", "TOKEN"),
                "timestamp": t.get("block", {}).get("timestamp", {}).get("time", datetime.utcnow().isoformat()),
                "receiver_entity": t.get("exchange", {}).get("fullName", "DEX"),
                "is_terminal": False
            })
        return edges

class BridgeCollector(BaseCollector):
    """Fetches Cross-Chain Bridge interactions."""
    # Stub for Bridge logic
    def get_query(self) -> str: return "query { ethereum { blocks { count } } }"
    def get_variables(self, address: str) -> dict: return {}
    def parse_response(self, data: dict, address: str) -> list: return []
