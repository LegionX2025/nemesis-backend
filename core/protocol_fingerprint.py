import logging
from typing import Dict, Any, List

logger = logging.getLogger("NEMESIS.GBIO.ProtocolFingerprint")

class ProtocolFingerprintEngine:
    """
    Tier-11 Protocol Fingerprinting Engine.
    Correlates target contracts, decoded events, and transfer types against 
    known global protocol profiles (DEXs, Mixers, Bridges, Lending Markets).
    """
    
    def __init__(self):
        self._initialize_profiles()

    def _initialize_profiles(self):
        """
        Loads behavioral and structural profiles of major DeFi protocols.
        """
        self.profiles = {
            "uniswap_v2": {
                "name": "Uniswap V2",
                "category": "DEX",
                "risk_tier": "LOW",
                "indicators": {
                    "event_topics": [
                        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822" # Swap
                    ],
                    "routers": ["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"]
                }
            },
            "uniswap_v3": {
                "name": "Uniswap V3",
                "category": "DEX",
                "risk_tier": "LOW",
                "indicators": {
                    "event_topics": [
                        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67" # Swap
                    ],
                    "routers": ["0xE592427A0AEce92De3Edee1F18E0157C05861564"]
                }
            },
            "tornado_cash": {
                "name": "Tornado Cash",
                "category": "MIXER",
                "risk_tier": "CRITICAL",
                "indicators": {
                    "event_topics": [
                        "0xa945e51eac50047228d17961bbfb912c4161a067ff505ad42270b213b3af572e", # Deposit
                        "0x8e1548ba335e3bce7fb4ffc70f80bc2cd1c84177eb1c5213b1940dbcb1da94d3"  # Withdrawal
                    ],
                    "selectors": ["0xb438689f", "0x21a0adb6"]
                }
            },
            "aave_v3": {
                "name": "Aave V3",
                "category": "LENDING",
                "risk_tier": "LOW",
                "indicators": {
                    "event_topics": [
                        "0x2b627736bca15cd5381dcf80b0bf11fd197d01a037c52b927a881a10fb73ba61", # Deposit
                        "0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac"  # Flashloan
                    ]
                }
            },
            "stargate_finance": {
                "name": "Stargate Finance (LayerZero)",
                "category": "BRIDGE",
                "risk_tier": "MEDIUM",
                "indicators": {
                    "event_topics": [
                        "0x346b0fa3facc5c1cbddb49ebce3f8b056ce8ccfa6dfaf4c3e3da54c8789bc5bf" # Send
                    ]
                }
            }
        }

    async def identify(self, raw_tx: Dict[str, Any], decoded_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes fingerprint matching against the transaction and its decoded payload.
        """
        tx_hash = raw_tx.get("hash", "UNKNOWN_HASH")
        logger.info(f"[ProtocolFingerprint] Fingerprinting transaction {tx_hash}")

        to_address = raw_tx.get("to", "").lower()
        events = decoded_data.get("events", [])
        selector = decoded_data.get("function_selector", None)

        matched_protocols = []

        # Evaluate against all profiles
        for protocol_id, profile in self.profiles.items():
            indicators = profile["indicators"]
            score = 0.0
            total_checks = 0

            # 1. Router / Contract matching
            if "routers" in indicators:
                total_checks += 1
                if any(to_address == router.lower() for router in indicators["routers"]):
                    score += 1.0

            # 2. Event Topic matching
            if "event_topics" in indicators and events:
                total_checks += 1
                for event in events:
                    topics = event.get("topics", [])
                    if topics and topics[0] in indicators["event_topics"]:
                        score += 1.0
                        break

            # 3. Selector matching
            if "selectors" in indicators and selector:
                total_checks += 1
                if selector in indicators["selectors"]:
                    score += 1.0

            # Calculate Confidence Match
            if score > 0:
                confidence = score / total_checks if total_checks > 0 else 0
                if confidence > 0.4:
                    matched_protocols.append({
                        "protocol_id": protocol_id,
                        "name": profile["name"],
                        "category": profile["category"],
                        "risk_tier": profile["risk_tier"],
                        "confidence": confidence
                    })

        # Sort by confidence
        matched_protocols.sort(key=lambda x: x["confidence"], reverse=True)

        if matched_protocols:
            primary = matched_protocols[0]
            return {
                "is_identified": True,
                "primary_protocol": primary["name"],
                "category": primary["category"],
                "risk_tier": primary["risk_tier"],
                "confidence": primary["confidence"],
                "all_matches": matched_protocols
            }

        return {
            "is_identified": False,
            "primary_protocol": "UNKNOWN_PROTOCOL",
            "category": "UNKNOWN",
            "risk_tier": "UNKNOWN",
            "confidence": 0.0,
            "all_matches": []
        }
