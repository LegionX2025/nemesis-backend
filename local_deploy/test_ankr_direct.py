import asyncio
import aiohttp
import json
import os

async def test_ankr():
    ankr_key = "d0ebdc10f7a98d2c08105ddcef64d9353e5b92e1d59e545debed8af8bce60fbc"
    url = f"https://rpc.ankr.com/multichain/{ankr_key}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "ankr_getTransactionsByAddress",
        "params": {
            "blockchain": ["bsc", "eth"],
            "address": ["0x030c0c65DBb914e423992F35b4Fe956F5E90b045"],
            "descOrder": True
        },
        "id": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as r:
            data = await r.json()
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(test_ankr())
