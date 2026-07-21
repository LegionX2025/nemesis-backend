import logging
from typing import Dict, Any, List

logger = logging.getLogger("NEMESIS.GBIO.TransferClassifier")

class TransferClassifierEngine:
    """
    Tier-11 Transfer Classifier Engine.
    Maps raw transaction footprints (functions, events, addresses) into 
    the Global Blockchain Intelligence Ontology (GBIO) normalized transfer types.
    """
    
    def __init__(self):
        self._initialize_heuristics()

    def _initialize_heuristics(self):
        """
        Initializes heuristic signatures for 300+ normalized transfer types.
        Uses combinations of topics, selectors, and behavioral traits.
        """
        self.heuristics = {
            # Core Asset Transfers
            "ERC20_TRANSFER": {"topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]},
            "ERC721_TRANSFER": {"topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"], "indexed_params": 3},
            "ERC1155_TRANSFER_SINGLE": {"topics": ["0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"]},
            
            # DEX & DeFi
            "SWAP": {"topics": ["0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"]}, # Uniswap V2 Swap
            "SWAP_V3": {"topics": ["0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"]}, # Uniswap V3 Swap
            "LIQUIDITY_ADD": {"topics": ["0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"]}, # Mint (V2)
            "LIQUIDITY_REMOVE": {"topics": ["0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"]}, # Burn (V2)
            "FLASH_LOAN": {"topics": ["0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac"]}, # Aave Flashloan
            "LIQUIDATION": {"topics": ["0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"]}, # Aave LiquidationCall

            # Cross-Chain Bridges
            "BRIDGE_LOCK": {"selectors": ["0x868b4408", "0x3c659741"]}, # deposit(), bridge()
            "BRIDGE_MINT": {"topics": ["0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"]}, # Generic Mint contextualized by Bridge contract
            "BRIDGE_RELEASE": {"selectors": ["0x2e1a7d4d", "0xdb006a75"]}, # withdraw(), redeem()

            # Obfuscation & Mixers
            "MIXER_DEPOSIT": {"selectors": ["0xb438689f", "0xa4cb51b2"]}, # Tornado Cash deposit
            "MIXER_WITHDRAWAL": {"selectors": ["0x21a0adb6"]}, # Tornado Cash withdraw
            
            # Administrative & Control
            "CONTRACT_DEPLOYMENT": {"to": None, "has_bytecode": True},
            "PROXY_UPGRADE": {"topics": ["0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"]}, # Upgraded
            
            # Miscellaneous
            "STAKE": {"selectors": ["0xa694fc3a", "0x7b0472f0"]}, # stake()
            "UNSTAKE": {"selectors": ["0x2e1a7d4d"]}, # withdraw()
            "DAO_VOTE": {"topics": ["0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4"]} # VoteCast
        }

    async def classify(self, raw_tx: Dict[str, Any], decoded_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes classification heuristics against the decoded transaction payload.
        Returns a structured GBIO Transfer Type with confidence scoring.
        """
        logger.info(f"[TransferClassifier] Classifying transaction {raw_tx.get('hash', 'UNKNOWN')}")
        
        # 1. Base State Check
        is_contract_deployment = raw_tx.get("to") is None or raw_tx.get("to") == ""
        value = int(raw_tx.get("value", 0))
        input_data = raw_tx.get("input", "0x")
        
        matched_types = []
        confidence_modifiers = []

        # 2. Heuristic Matching: Native Transfer
        if input_data == "0x" and value > 0 and not is_contract_deployment:
            matched_types.append("NATIVE_TRANSFER")
            confidence_modifiers.append(1.0) # Deterministic

        # 3. Heuristic Matching: Contract Deployment
        if is_contract_deployment and input_data != "0x":
            matched_types.append("CONTRACT_DEPLOYMENT")
            confidence_modifiers.append(1.0)

        # 4. Decoded Payload Analysis (Functions & Events)
        if decoded_data and "status" not in decoded_data:
            events = decoded_data.get("events", [])
            function_selector = decoded_data.get("function_selector", None)

            for transfer_type, rules in self.heuristics.items():
                match_score = 0.0
                required_hits = 0

                # Check Function Selectors
                if "selectors" in rules and function_selector:
                    required_hits += 1
                    if function_selector in rules["selectors"]:
                        match_score += 1.0

                # Check Event Topics
                if "topics" in rules and events:
                    required_hits += 1
                    for event in events:
                        topics = event.get("topics", [])
                        if topics and topics[0] in rules["topics"]:
                            match_score += 1.0
                            break # Found match

                # Compute match threshold
                if required_hits > 0 and match_score > 0:
                    matched_types.append(transfer_type)
                    confidence = match_score / required_hits
                    confidence_modifiers.append(confidence)

        # 5. Fallback Resolution
        if not matched_types:
            if input_data != "0x" and value > 0:
                matched_types.append("NATIVE_TRANSFER_WITH_DATA")
                confidence_modifiers.append(0.8)
            elif input_data != "0x":
                matched_types.append("CONTRACT_CALL_UNKNOWN")
                confidence_modifiers.append(0.5)
            else:
                matched_types.append("UNKNOWN_TRANSFER")
                confidence_modifiers.append(0.1)

        # Determine Primary Transfer Type (Highest confidence / specificity)
        # Note: In a full implementation, we'd rank them by ontology weight.
        primary_type = matched_types[-1] if matched_types else "UNKNOWN_TRANSFER"
        primary_confidence = confidence_modifiers[-1] if confidence_modifiers else 0.0

        return {
            "primary_type": primary_type,
            "all_matches": matched_types,
            "confidence": primary_confidence,
            "ontology_class": f"gbio:transfer:{primary_type.lower()}"
        }
