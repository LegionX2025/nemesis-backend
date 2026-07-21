import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("OmniParser")

class OmniParser:
    """
    Parses raw blockchain data (events, logs, internal txs) into standardized
    MongoDB state-transition schema events and edges.
    """
    
    @staticmethod
    def parse_evm_event(log: Dict[str, Any], decoded_signature: str = None) -> List[Dict[str, Any]]:
        """
        Takes an EVM log/event and returns a list of state_edges and events.
        """
        edges = []
        sig = decoded_signature or log.get("method", "").lower()
        
        from_address = log.get("from", "")
        to_address = log.get("to", "")
        value = log.get("value", "0")
        tx_hash = log.get("hash", log.get("transactionHash", ""))
        token = log.get("tokenSymbol", "ETH")
        chain = log.get("chain", "eth")

        edge_type = "TRANSFER"
        
        if sig:
            if "swap" in sig or "exactinput" in sig or "exactoutput" in sig:
                edge_type = "SWAP"
            elif "mint" in sig:
                edge_type = "MINT"
            elif "burn" in sig:
                edge_type = "BURN"
            elif "deposit" in sig or "lock" in sig:
                edge_type = "LOCK"
            elif "withdraw" in sig or "release" in sig:
                edge_type = "RELEASE"
            elif "borrow" in sig:
                edge_type = "BORROW"
            elif "repay" in sig:
                edge_type = "REPAY"
        else:
            # Fallback based on addresses
            if from_address == "0x0000000000000000000000000000000000000000":
                edge_type = "MINT"
            elif to_address == "0x0000000000000000000000000000000000000000" or to_address == "0x000000000000000000000000000000000000dead":
                edge_type = "BURN"
                
        edge = {
            "from": from_address,
            "to": to_address,
            "edge_type": edge_type,
            "tx_hash": tx_hash,
            "chain": chain,
            "asset": token,
            "amount": value,
            "confidence": 1.0
        }
        edges.append(edge)
        return edges

    @staticmethod
    def parse_solana_log(log: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses Solana program logs and instructions.
        """
        edges = []
        tx_hash = log.get("signature", "")
        logs = log.get("logs", [])
        
        # Heuristic log parsing
        for line in logs:
            line_lower = line.lower()
            if "instruction: transfer" in line_lower:
                edges.append({
                    "from": log.get("feePayer", "unknown"),
                    "to": "unknown", # Needs deep parsing of instruction data
                    "edge_type": "TRANSFER",
                    "tx_hash": tx_hash,
                    "chain": "sol",
                    "asset": "SOL/SPL",
                    "amount": "0",
                    "confidence": 0.8
                })
            elif "instruction: mintto" in line_lower:
                edges.append({
                    "from": "0x00...00",
                    "to": log.get("feePayer", "unknown"),
                    "edge_type": "MINT",
                    "tx_hash": tx_hash,
                    "chain": "sol",
                    "asset": "SPL",
                    "amount": "0",
                    "confidence": 0.9
                })
            elif "instruction: swap" in line_lower or "raydium" in line_lower or "orca" in line_lower:
                edges.append({
                    "from": log.get("feePayer", "unknown"),
                    "to": "DEX_POOL",
                    "edge_type": "SWAP",
                    "tx_hash": tx_hash,
                    "chain": "sol",
                    "asset": "SPL",
                    "amount": "0",
                    "confidence": 0.9
                })
        
        # Fallback if no specific instructions matched
        if not edges and log.get("feePayer"):
            edges.append({
                "from": log.get("feePayer"),
                "to": "unknown",
                "edge_type": "TRANSFER",
                "tx_hash": tx_hash,
                "chain": "sol",
                "asset": "SOL",
                "amount": "0",
                "confidence": 0.5
            })
            
        return edges

    @staticmethod
    def parse_tron_internal(tx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses Tron internal transactions (e.g. from smart contracts).
        """
        edges = []
        edge_type = "TRANSFER"
        # TRON often has trc20TransferInfo or internal_transactions
        if tx.get("token_info") or tx.get("trc20TransferInfo"):
            edge_type = "TRANSFER"
        
        edges.append({
            "from": tx.get("ownerAddress", tx.get("from", "")),
            "to": tx.get("toAddress", tx.get("to", "")),
            "edge_type": edge_type,
            "tx_hash": tx.get("hash", ""),
            "chain": "tron",
            "asset": tx.get("token_info", {}).get("symbol", "TRX"),
            "amount": tx.get("amount", "0"),
            "confidence": 0.95
        })
        return edges

    @staticmethod
    def extract_identity_artifacts(tx: Dict[str, Any], chain: str) -> List[Dict[str, Any]]:
        """
        Extracts XRP destination tags, Stellar memos, Hedera topics into identity artifacts.
        """
        artifacts = []
        tx_hash = tx.get("hash", "")
        
        if chain == "xrp":
            tag = tx.get("DestinationTag")
            if tag:
                artifacts.append({
                    "type": "destination_tag",
                    "value": str(tag),
                    "linked_entities": [tx.get("Destination", ""), tx.get("Account", "")],
                    "chain": chain,
                    "tx_hash": tx_hash
                })
        elif chain == "xlm":
            memo = tx.get("memo")
            if memo:
                artifacts.append({
                    "type": "memo",
                    "value": str(memo),
                    "linked_entities": [tx.get("from", ""), tx.get("to", "")],
                    "chain": chain,
                    "tx_hash": tx_hash
                })
        elif chain == "hedera":
            memo = tx.get("memo", "")
            if memo:
                artifacts.append({
                    "type": "memo",
                    "value": str(memo),
                    "linked_entities": [tx.get("from", ""), tx.get("to", "")],
                    "chain": chain,
                    "tx_hash": tx_hash
                })
                
        return artifacts
