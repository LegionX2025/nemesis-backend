import asyncio
import aiohttp
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from services.trace_engine import auto_compute_loss_amount, detect_chain

async def main():
    print(detect_chain("0x4a1801c1074e50d53c3d0b271d18721c4355529f79b0bf3b2f5b66d40c034cb8", "ETHEREUM"))
    print(detect_chain("0x4a1801c1074e50d53c3d0b271d18721c4355529f79b0bf3b2f5b66d40c034cb8", "AUTO"))
    res = await auto_compute_loss_amount(["0x4a1801c1074e50d53c3d0b271d18721c4355529f79b0bf3b2f5b66d40c034cb8"], "AUTO")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
