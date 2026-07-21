import asyncio
import aiohttp
import json

async def fetch():
    addr = 'bc1qprtnld4jf43uq6h9y460d76annunqag9dhcv52'
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://mempool.space/api/address/{addr}/txs') as r:
                txs = await r.json()
        
        with open('test_btc_out.txt', 'w') as f:
            f.write(f'Fetched {len(txs)} txs\n')
            for tx in txs:
                is_sender = any(i.get('prevout', {}).get('scriptpubkey_address', '').lower() == addr for i in tx.get('vin', []))
                is_receiver = any(o.get('scriptpubkey_address', '').lower() == addr for o in tx.get('vout', []))
                f.write(f'txid={tx.get("txid")} is_sender={is_sender} is_receiver={is_receiver}\n')
                
                if is_sender:
                    for o in tx.get('vout', []):
                        to = o.get('scriptpubkey_address', '').lower()
                        amt = int(o.get('value', 0)) / 1e8
                        f.write(f'  Outbound: {to} (amt={amt})\n')
                elif is_receiver:
                    for i in tx.get('vin', []):
                        f_addr = i.get('prevout', {}).get('scriptpubkey_address', '').lower()
                        amt = int(i.get('prevout', {}).get('value', 0)) / 1e8
                        f.write(f'  Inbound: {f_addr} (amt={amt})\n')
    except Exception as e:
        with open('test_btc_out.txt', 'w') as f:
            f.write(str(e))

asyncio.run(fetch())
