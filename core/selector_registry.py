import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("NEMESIS.GBIO.SelectorRegistry")

class SelectorRegistry:
    """
    Tier-11 Selector & Event Signature Registry.
    Provides O(1) lookups for function selectors (4-byte) and event topics (32-byte)
    to enable heuristic decoding when smart contract ABIs are unverified or unavailable.
    """
    
    def __init__(self):
        self.function_selectors: Dict[str, str] = {}
        self.event_signatures: Dict[str, str] = {}
        self._load_core_signatures()

    def _load_core_signatures(self):
        """
        Loads the most critical DeFi, Mixer, Bridge, and Token signatures directly into memory.
        In a production scenario, this would be backed by a local SQLite/LevelDB snapshot 
        of the Ethereum Signature Database (4byte.directory).
        """
        logger.info("[SelectorRegistry] Loading core cryptographic signatures...")
        
        # --- Core Token Standards ---
        self.function_selectors.update({
            "0xa9059cbb": "transfer(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0x42842e0e": "safeTransferFrom(address,address,uint256)"
        })
        self.event_signatures.update({
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
            "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)"
        })

        # --- DEX & AMM (Uniswap V2 / V3 / Curve) ---
        self.function_selectors.update({
            "0x38ed1739": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
            "0x7ff36ab5": "swapExactETHForTokens(uint256,address[],address,uint256)",
            "0x18cbafe5": "swapExactTokensForETH(uint256,uint256,address[],address,uint256)",
            "0xe8e33700": "addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)",
            "0xf305d719": "addLiquidityETH(address,uint256,uint256,uint256,address,uint256)",
            "0xbaa2abde": "removeLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)"
        })
        self.event_signatures.update({
            "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Swap(address,uint256,uint256,uint256,uint256,address)",
            "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f": "Mint(address,uint256,uint256)",
            "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496": "Burn(address,uint256,uint256,address)"
        })

        # --- Cross-Chain Bridges ---
        self.function_selectors.update({
            "0x868b4408": "deposit(uint256)", # Generic bridge deposit
            "0x3c659741": "bridge(address,uint256,uint256)",
            "0x2e1a7d4d": "withdraw(uint256)"
        })

        # --- Obfuscation & Mixers (Tornado Cash) ---
        self.function_selectors.update({
            "0xb438689f": "deposit(bytes32)",
            "0x21a0adb6": "withdraw(bytes,bytes32,bytes32,address,address,uint256,uint256)"
        })
        self.event_signatures.update({
            "0xa945e51eac50047228d17961bbfb912c4161a067ff505ad42270b213b3af572e": "Deposit(bytes32,uint32,uint256)",
            "0x8e1548ba335e3bce7fb4ffc70f80bc2cd1c84177eb1c5213b1940dbcb1da94d3": "Withdrawal(address,bytes32,address,uint256)"
        })

        # --- Lending (Aave / Compound) ---
        self.function_selectors.update({
            "0xe8eda9df": "deposit(address,uint256,address,uint16)", # Aave V3
            "0x69328dec": "withdraw(address,uint256,address)", # Aave V3
            "0xab9c4b5d": "borrow(address,uint256,uint256,uint16,address)", # Aave V3
            "0x5ce1e598": "repay(address,uint256,uint256,address)", # Aave V3
            "0x631042c8": "flashLoan(address,address[],uint256[],uint256[],address,bytes,uint16)" # Aave Flashloan
        })

    def get_function_name(self, hex_selector: str) -> Optional[str]:
        """Looks up a 4-byte selector (e.g., '0xa9059cbb') and returns the canonical signature."""
        hex_selector = hex_selector.lower()
        if not hex_selector.startswith("0x"):
            hex_selector = f"0x{hex_selector}"
        return self.function_selectors.get(hex_selector)

    def get_event_name(self, hex_topic: str) -> Optional[str]:
        """Looks up a 32-byte event topic (e.g., '0xddf2...') and returns the canonical signature."""
        hex_topic = hex_topic.lower()
        if not hex_topic.startswith("0x"):
            hex_topic = f"0x{hex_topic}"
        return self.event_signatures.get(hex_topic)
