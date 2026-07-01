import asyncio
import aiohttp
import json

async def test_apis():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    address = "0x7675dc2856fca0c22ed3c57979388fbf236de57f"
    
    urls = [
        ("ARB V1", f"https://api.arbiscan.io/api?module=account&action=txlist&address={address}&apikey=YourApiKeyToken"),
        ("ARB V2", f"https://api.arbiscan.io/v2/api?chainid=42161&module=account&action=txlist&address={address}&apikey=YourApiKeyToken"),
        ("POLY V1", f"https://api.polygonscan.com/api?module=account&action=txlist&address={address}&apikey=YourApiKeyToken"),
        ("POLY V2", f"https://api.polygonscan.com/v2/api?chainid=137&module=account&action=txlist&address={address}&apikey=YourApiKeyToken"),
        ("ETH V2", f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={address}&apikey=YourApiKeyToken")
    ]

    async with aiohttp.ClientSession() as session:
        for name, url in urls:
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
