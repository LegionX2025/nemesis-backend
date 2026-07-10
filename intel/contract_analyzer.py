import logging
import re

logger = logging.getLogger("NEMESIS.v32.ContractAnalyzer")

class ContractAnalyzer:
    def __init__(self):
        # EIP-1967 Proxy storage slots
        self.eip1967_logic_slot = "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        self.eip1967_beacon_slot = "a3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
        
    def analyze(self, bytecode: str) -> dict:
        if not bytecode or bytecode == "0x" or len(bytecode) < 4:
            return {"type": "EOA", "is_proxy": False}
            
        is_proxy = False
        implementation = None
        
        # Heuristic EIP-1967 detection
        if "363d3d373d3d3d363d73" in bytecode or self.eip1967_logic_slot in bytecode:
            is_proxy = True
            implementation = "Requires eth_getStorageAt for slot 0x360894..."
            
        # Basic 4-byte selector extraction
        # PUSH4 0xXXXXXXXX followed by EQ (14)
        selectors = re.findall(r'63([a-f0-9]{8})14', bytecode)
        
        return {
            "type": "CONTRACT",
            "is_proxy": is_proxy,
            "implementation": implementation,
            "function_selectors": list(set(selectors))
        }
