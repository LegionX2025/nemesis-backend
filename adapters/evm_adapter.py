import asyncio
import logging
from web3 import Web3

logger = logging.getLogger("NEMESIS.v32.EVMAdapter")

class EVMAdapter:
    def __init__(self, rpc_url: str = "https://cloudflare-eth.com"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        logger.info(f"Initialized EVM Adapter connected to {rpc_url}")

    async def fetch_bytecode(self, address: str) -> str:
        try:
            # Wrap synchronous web3 call in an async executor
            loop = asyncio.get_event_loop()
            bytecode = await loop.run_in_executor(None, self.w3.eth.get_code, Web3.to_checksum_address(address))
            return bytecode.hex()
        except Exception as e:
            logger.error(f"Failed to fetch bytecode for {address}: {e}")
            return "0x"

    async def debug_trace_transaction(self, tx_hash: str) -> dict:
        """
        Premium RPCs required for debug_traceTransaction.
        Fetches full internal call traces (CALL, DELEGATECALL, STATICCALL).
        """
        logger.info(f"Fetching debug_traceTransaction for {tx_hash}")
        try:
            # Note: Many public endpoints disable this.
            loop = asyncio.get_event_loop()
            trace = await loop.run_in_executor(None, self.w3.provider.make_request, "debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
            return trace
        except Exception as e:
            logger.warning(f"debug_traceTransaction not supported or failed: {e}")
            return {}
