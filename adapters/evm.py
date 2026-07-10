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

    async def get_logs(self, address: str, chain: str = "ETH", from_block="0x0", to_block="latest"):
        logger.info(f"Fetching EVM logs for {address} on {chain}")
        rpc_url = self.eth_rpc
        if chain == "POLYGON": rpc_url = self.polygon_rpc
        if chain == "BSC": rpc_url = self.bsc_rpc
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getLogs",
            "params": [{"address": address, "fromBlock": from_block, "toBlock": to_block}],
            "id": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(rpc_url, json=payload, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        return data.get("result", [])
        except Exception as e:
            logger.error(f"EVM get_logs error on {chain}: {e}")
        return []

    async def get_internal_calls(self, tx_hash: str, chain: str = "ETH"):
        # Uses debug_traceTransaction if available
        rpc_url = self.eth_rpc
        payload = {
            "jsonrpc": "2.0",
            "method": "debug_traceTransaction",
            "params": [tx_hash, {"tracer": "callTracer"}],
            "id": 1
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(rpc_url, json=payload, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        return data.get("result", {})
        except Exception as e:
            logger.error(f"EVM debug_trace error: {e}")
        return {}

    def get_bytecode(self, address: str, chain: str = "ETH"):
        try:
            w3_instance = self.w3.get(chain.upper(), self.w3["ETH"])
            checksum_addr = Web3.to_checksum_address(address)
            code = w3_instance.eth.get_code(checksum_addr)
            return code.hex()
        except Exception as e:
            logger.warning(f"Failed to get bytecode for {address} on {chain}: {e}")
            return "0x"
