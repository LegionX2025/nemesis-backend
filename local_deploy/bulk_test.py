import asyncio
import httpx
import json

wallets = [
    "bc1qguj54d66l502pwvft3zjrgwtmvhhq88nsaj7t6",
    "0x2a91386cEdb02D0d1fc37a262B07d458A015F06F",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "0xD6094943979AfB5d2748FBB84788Aa4D2b0bd857",
    "rJnLjofJ25FQc5wXgac4LCJFC364hptbJx",
    "rhwTCnnXrunzYGAe9GVEqcbUx7PUbTHWsm",
    "01beef7b5cb9814c9457048d3e444e629d555ef53a064dc4f69b804234eb4da4",
    "C46E163E55837748A2F623D55898B281B517654AFE06CCE6AC69BB8B0BF4553C",
    "0x353085f3c41a3c5475df2f5542dfd2d2757cd73ca2f6bf9c0b740ef0cdb07490",
    "0x33c5e72fcebed5d255eb396017982ad2cdceb2ef97275c58d04889ab2c52fac2",
    "0x69F8c4c19A3Fb24859fc9E0DacfD554c17958d75",
    "0x4Cbcff095bdb49885439c4B4F3c8dEC287F942d2",
    "0x030c0c65DBb914e423992F35b4Fe956F5E90b045",
    "0x7B9123262ad3b1F3Be48046B7D1e8f3Cd50B33D9",
    "0x97F1b05adb4FCCCA8a1a34E4801079547351419d",
    "0x36043C1860998b53dfeF070947f54a7B4567e9AC",
    "0x819c8aE7eA9FD880426fad62639D355d6aFC6921",
    "0xc28B3feFd967e573834F87400A65395e1C63BA99",
    "TJNT1H28om6hbxKwdDAcQxiGQwgrs7GDF5",
    "TSZGemBcmawToBxDvLvVzqPuav5qmqbHVK",
    "TVLAAu2vokqc9rekyUXqPyNLL5tPTBy8m5",
    "TVNcfk3b7Qq832WFg1oRpK38jnq4sMVFeX",
    "TT298Xjy7S7NuSa88diu5YY49KFEATb3N6",
    "TLrqCVpWW3g1vMNhfFKjwDa9MjAK5b12zA"
]

async def test_all_wallets():
    print(f"Starting bulk intelligence testing for {len(wallets)} targets...")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        for address in wallets:
            print(f"[*] Extracting OSINT for: {address}")
            try:
                # Query the backend directly
                response = await client.get(f"http://127.0.0.1:8088/api/nemesis_id/intel/{address}")
                if response.status_code == 200:
                    data = response.json()
                    
                    # Highlight Malicious wallets in RED
                    color = "\033[91m" if data.get("is_malicious") else "\033[92m"
                    reset = "\033[0m"
                    
                    malicious_status = f"{color}MALICIOUS: {data.get('is_malicious')}{reset}"
                    tags = data.get('scraped_tags', [])
                    tag_str = ", ".join(tags) if tags else "None"
                    
                    print(f"    -> {malicious_status}")
                    print(f"    -> OSINT Entity: {data.get('osint_intel')}")
                    print(f"    -> Extracted Tags: {tag_str}")
                else:
                    print(f"    -> [!] API Error: HTTP {response.status_code}")
            except Exception as e:
                print(f"    -> [!] Connection Error (Is backend running?): {e}")
            print("-" * 60)

if __name__ == "__main__":
    import os
    os.system('color')
    asyncio.run(test_all_wallets())
