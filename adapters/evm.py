import os
import aiohttp
import asyncio
import logging
from web3 import Web3

logger = logging.getLogger("OmniChainEngine.EVM")

class EVMAdapter:
    def __init__(self):
        self.eth_rpc = os.getenv("RPC_ETH", "https://eth.llamarpc.com")
        self.polygon_rpc = os.getenv("RPC_POLYGON", "https://polygon.llamarpc.com")
        self.bsc_rpc = os.getenv("RPC_BSC", "https://binance.llamarpc.com")
        
        self.w3 = {
            "ETH": Web3(Web3.HTTPProvider(self.eth_rpc)),
            "POLYGON": Web3(Web3.HTTPProvider(self.polygon_rpc)),
            "BSC": Web3(Web3.HTTPProvider(self.bsc_rpc))
        }

    async def get_transactions(self, address: str, chain: str = "ETH"):
        # Placeholder for actual API fetching logic (Etherscan, etc.)
        # Since this is v32, we abstract this out from trace_engine.py
        # Fallback to Etherscan if RPC archive node is not available
        logger.info(f"Fetching EVM {chain} transactions for {address}")
        return []

    def get_bytecode(self, address: str, chain: str = "ETH"):
        try:
            w3_instance = self.w3.get(chain.upper(), self.w3["ETH"])
            checksum_addr = Web3.to_checksum_address(address)
            code = w3_instance.eth.get_code(checksum_addr)
            return code.hex()
        except Exception as e:
            logger.warning(f"Failed to get bytecode for {address} on {chain}: {e}")
            return "0x"
