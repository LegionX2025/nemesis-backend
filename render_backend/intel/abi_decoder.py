import json
import logging
from web3 import Web3

logger = logging.getLogger("OmniChainEngine.ABI")

class ABIDecoder:
    def __init__(self):
        # Basic signatures for common DeFi interactions (4-byte method selectors)
        self.method_signatures = {
            "0xa9059cbb": "transfer(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0xd0e30db0": "deposit()",
            "0x2e1a7d4d": "withdraw(uint256)",
            "0x38ed1739": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
            "0xb6f9de95": "swapExactETHForTokens(uint256,address[],address,uint256)"
        }
        
        # Event Signature Hashes (topics[0])
        self.event_signatures = {
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer",
            "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval",
            "0xe1cb0e51049e083c21a1ce0ffba253b2ce24e54806a6b5711ab4d3fc827f311c": "Deposit",
            "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65": "Withdrawal",
            "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Swap", # Uniswap V2 Swap
            "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67": "Swap", # Uniswap V3 Swap
            "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f": "Mint", # Uniswap V2 Mint
            "0xa0715619ce10bd5070054ccbc0153406e1ccab6a30c458390b4d45d654570081": "Burn", # Uniswap V2 Burn
            "0x8c0050800d922bc266f81a1795cda28da1ba9a3cc009089ea4e7edb7d7f72473": "BridgeDeposit", # Typical lock
            "0x17ed3f58a36efd7a04ab4d7f516a24eb5ef74a441e8cba50b0673322bc8c51dd": "BridgeWithdrawal" # Typical release
        }

    def decode_input(self, input_data: str):
        if not input_data or input_data == "0x":
            return None
        
        selector = input_data[:10].lower()
        if selector in self.method_signatures:
            return {
                "signature": self.method_signatures[selector],
                "type": "KNOWN_METHOD",
                "raw_input": input_data
            }
        return {
            "signature": selector,
            "type": "UNKNOWN_METHOD",
            "raw_input": input_data
        }

    def decode_log(self, log: dict):
        topics = log.get("topics", [])
        if not topics:
            return None
        
        topic0 = topics[0].lower()
        event_name = self.event_signatures.get(topic0, "UnknownEvent")
        
        # Determine intent (MINT/BURN/LOCK/RELEASE/SWAP/TRANSFER)
        intent = "UNKNOWN"
        if event_name == "Transfer":
            if len(topics) >= 3:
                src = "0x" + topics[1][-40:]
                dst = "0x" + topics[2][-40:]
                if src == "0x0000000000000000000000000000000000000000":
                    intent = "MINT"
                elif dst == "0x0000000000000000000000000000000000000000":
                    intent = "BURN"
                else:
                    intent = "TRANSFER"
        elif event_name == "Deposit" or "Lock" in event_name:
            intent = "LOCK"
        elif event_name == "Withdrawal" or "Release" in event_name:
            intent = "RELEASE"
        elif event_name == "Swap":
            intent = "SWAP"
        elif event_name == "Mint":
            intent = "MINT"
        elif event_name == "Burn":
            intent = "BURN"
            
        return {
            "event_name": event_name,
            "topic0": topic0,
            "intent": intent,
            "topics": topics,
            "data": log.get("data", "0x")
        }

    def analyze_bytecode(self, bytecode: str):
        if not bytecode or bytecode == "0x":
            return "EOA"
        
        bytecode = bytecode.lower()
        # Proxy detection EIP-1967
        if "363d3d373d3d3d363d73" in bytecode:
            return "EIP_1967_PROXY"
            
        if "60806040" in bytecode or "60606040" in bytecode: 
            if "a9059cbb" in bytecode and "18160ddd" in bytecode: # transfer & totalSupply
                return "ERC20_CONTRACT"
            if "d78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822" in bytecode:
                return "UNISWAP_V2_POOL"
            return "GENERIC_CONTRACT"
        return "UNKNOWN_CONTRACT"
