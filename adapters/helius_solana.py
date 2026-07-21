import aiohttp
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

async def fetch_helius_transactions(address: str, max_pages: int = 1) -> List[Dict]:
    """
    Fetch parsed Solana transactions using the Helius API.
    """
    api_key = os.getenv("HELIUS_API_KEY", "")
    if not api_key:
        logger.warning("HELIUS_API_KEY not found. Using fallback public RPC logic.")
        return []

    url = f"https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={api_key}"
    transactions = []
    
    async with aiohttp.ClientSession() as session:
        last_signature = None
        for i in range(max_pages):
            req_url = f"{url}&before={last_signature}" if last_signature else url
            try:
                async with session.get(req_url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            break
                            
                        for tx in data:
                            # Parse out native transfers or token transfers
                            tx_type = tx.get("type", "UNKNOWN")
                            timestamp = tx.get("timestamp", 0)
                            signature = tx.get("signature", "")
                            fee = tx.get("fee", 0)
                            
                            native_transfers = tx.get("nativeTransfers", [])
                            for nt in native_transfers:
                                amount = nt.get("amount", 0) / 1e9 # SOL has 9 decimals
                                from_user = nt.get("fromUserAccount", "")
                                to_user = nt.get("toUserAccount", "")
                                
                                if amount > 0:
                                    transactions.append({
                                        "hash": signature,
                                        "from_addr": from_user,
                                        "to_addr": to_user,
                                        "amount": amount,
                                        "chain": "SOLANA",
                                        "timestamp": timestamp,
                                        "fee": fee / 1e9,
                                        "type": tx_type,
                                        "token": "SOL"
                                    })
                            
                            token_transfers = tx.get("tokenTransfers", [])
                            for tt in token_transfers:
                                amount = tt.get("tokenAmount", 0)
                                from_user = tt.get("fromUserAccount", "")
                                to_user = tt.get("toUserAccount", "")
                                mint = tt.get("mint", "")
                                
                                if amount > 0:
                                    transactions.append({
                                        "hash": signature,
                                        "from_addr": from_user,
                                        "to_addr": to_user,
                                        "amount": amount,
                                        "chain": "SOLANA",
                                        "timestamp": timestamp,
                                        "fee": fee / 1e9,
                                        "type": tx_type,
                                        "token": mint
                                    })
                        
                        last_signature = data[-1].get("signature")
                    else:
                        logger.error(f"Helius API error: {response.status}")
                        break
            except Exception as e:
                logger.error(f"Exception fetching Helius txs for {address}: {e}")
                break
                
    return transactions
