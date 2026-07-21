import aiohttp
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

async def fetch_horizon_transactions(address: str, max_pages: int = 1) -> List[Dict]:
    """
    Fetch XLM transactions using the native Horizon async API.
    """
    url = f"https://horizon.stellar.org/accounts/{address}/payments?limit=200"
    
    transactions = []
    
    async with aiohttp.ClientSession() as session:
        cursor = None
        for i in range(max_pages):
            req_url = f"{url}&cursor={cursor}" if cursor else url
            try:
                async with session.get(req_url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("_embedded", {}).get("records", [])
                        if not records:
                            break
                            
                        for record in records:
                            tx_hash = record.get("transaction_hash", "")
                            timestamp = record.get("created_at", "")
                            tx_type = record.get("type", "")
                            
                            if tx_type == "payment":
                                amount = float(record.get("amount", 0))
                                asset_type = record.get("asset_type", "")
                                token = "XLM" if asset_type == "native" else record.get("asset_code", "UNKNOWN")
                                
                                from_addr = record.get("from", "")
                                to_addr = record.get("to", "")
                                
                                if amount > 0:
                                    transactions.append({
                                        "hash": tx_hash,
                                        "from_addr": from_addr,
                                        "to_addr": to_addr,
                                        "amount": amount,
                                        "chain": "STELLAR",
                                        "timestamp": timestamp,
                                        "fee": 0, # fee is typically in the transaction endpoint, not payment endpoint
                                        "type": tx_type,
                                        "token": token
                                    })
                        
                        # Pagination cursor
                        next_link = data.get("_links", {}).get("next", {}).get("href")
                        if next_link:
                            # extract cursor from URL
                            import urllib.parse as urlparse
                            parsed = urlparse.urlparse(next_link)
                            params = urlparse.parse_qs(parsed.query)
                            cursor_list = params.get("cursor", [])
                            if cursor_list:
                                cursor = cursor_list[0]
                            else:
                                break
                        else:
                            break
                    else:
                        logger.error(f"Horizon API error: {response.status}")
                        break
            except Exception as e:
                logger.error(f"Exception fetching Horizon txs for {address}: {e}")
                break
                
    return transactions
