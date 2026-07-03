import json
import logging
from web3 import Web3

logger = logging.getLogger("OmniChainEngine.ABI")

class ABIDecoder:
    def __init__(self):
        # Basic signatures for common DeFi interactions
        self.signatures = {
            "0xa9059cbb": "transfer(address,uint256)",
            "0x23b872dd": "transferFrom(address,address,uint256)",
            "0x095ea7b3": "approve(address,uint256)",
            "0xd0e30db0": "deposit()",
            "0x2e1a7d4d": "withdraw(uint256)",
            "0x38ed1739": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
            "0xb6f9de95": "swapExactETHForTokens(uint256,address[],address,uint256)"
        }

    def decode_input(self, input_data: str):
        if not input_data or input_data == "0x":
            return None
        
        selector = input_data[:10]
        if selector in self.signatures:
            return {
                "signature": self.signatures[selector],
                "type": "KNOWN_METHOD",
                "raw_input": input_data
            }
        return {
            "signature": selector,
            "type": "UNKNOWN_METHOD",
            "raw_input": input_data
        }

    def analyze_bytecode(self, bytecode: str):
        if not bytecode or bytecode == "0x":
            return "EOA" # Externally Owned Account
        
        if "60806040" in bytecode: # Common solidity compiler init
            if "a9059cbb" in bytecode: # transfer selector
                return "ERC20_CONTRACT"
            return "GENERIC_CONTRACT"
        return "UNKNOWN_CONTRACT"
