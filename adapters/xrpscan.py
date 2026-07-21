import aiohttp
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

async def fetch_xrpscan_transactions(address: str, max_pages: int = 1) -> List[Dict]:
    """
    Fetch XRP transactions using the native XRPSCAN async API.
    """
    base_url = os.getenv("XRPSCAN_BASE_URL", "https://api.xrpscan.com/api/v1")
    url = f"{base_url}/account/{address}/transactions"
    
    transactions = []
    
    async with aiohttp.ClientSession() as session:
        marker = None
        for i in range(max_pages):
            req_url = f"{url}?marker={marker}" if marker else url
            try:
                async with session.get(req_url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        txs = data.get("transactions", [])
                        if not txs:
                            break
                            
                        for tx in txs:
                            tx_hash = tx.get("hash", "")
                            date = tx.get("date", "")
                            fee = float(tx.get("fee", 0)) / 1e6 # XRP has 6 drops
                            tx_type = tx.get("TransactionType", "")
                            
                            if tx_type == "Payment":
                                amount_data = tx.get("Amount", "0")
                                # Amount can be a string (XRP drops) or a dict (issued currency)
                                amount = 0.0
                                token = "XRP"
                                if isinstance(amount_data, str):
                                    amount = float(amount_data) / 1e6
                                elif isinstance(amount_data, dict):
                                    amount = float(amount_data.get("value", 0))
                                    token = amount_data.get("currency", "UNKNOWN")
                                    
                                from_addr = tx.get("Account", "")
                                to_addr = tx.get("Destination", "")
                                
                                if amount > 0:
                                    transactions.append({
                                        "hash": tx_hash,
                                        "from_addr": from_addr,
                                        "to_addr": to_addr,
                                        "amount": amount,
                                        "chain": "RIPPLE",
                                        "timestamp": date,
                                        "fee": fee,
                                        "type": tx_type,
                                        "token": token
                                    })
                        
                        marker = data.get("marker")
                        if not marker:
                            break
                    else:
                        logger.error(f"XRPSCAN API error: {response.status}")
                        break
            except Exception as e:
                logger.error(f"Exception fetching XRPSCAN txs for {address}: {e}")
                break
                
    return transactions
