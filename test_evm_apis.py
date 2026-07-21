import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_apis():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    address = "0x7675dc2856fca0c22ed3c57979388fbf236de57f"
    
    # 1. Polygon V1
    poly_key = os.getenv("POLYGONSCAN_API_KEY", "YourApiKeyToken")
    url_poly = f"https://api.polygonscan.com/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey={poly_key}"
    
    # 2. BSC V1
    bsc_key = os.getenv("BSCSCAN_API_KEY", "YourApiKeyToken")
    url_bsc = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey={bsc_key}"

    # 3. Arbitrum V1
    arb_key = os.getenv("ARBITRUMSCAN_API_KEY", "YourApiKeyToken")
    url_arb = f"https://api.arbiscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey={arb_key}"
    
    # 4. Ethereum V1
    eth_key = os.getenv("ETHERSCAN_API_KEY", "YourApiKeyToken")
    url_eth = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=5&sort=desc&apikey={eth_key}"

    async with aiohttp.ClientSession() as session:
        for name, url in [("POLYGON", url_poly), ("BSC", url_bsc), ("ARBITRUM", url_arb), ("ETHEREUM", url_eth)]:
            try:
                async with session.get(url, headers=headers) as r:
                    print(f"\n--- {name} ---")
                    print(f"Status: {r.status}")
                    text = await r.text()
                    try:
                        data = json.loads(text)
                        print(f"JSON: {json.dumps(data)[:200]}...")
                    except:
                        print(f"NON-JSON: {text[:200]}...")
            except Exception as e:
                print(f"Error: {e}")

asyncio.run(test_apis())
