import asyncio
import logging
import json
import os
from .scraper_engine import scraper_instance
from .api_rotator import api_rotator

logger = logging.getLogger("SwarmOrchestrator")

class SwarmOrchestrator:
    def __init__(self, max_concurrent=10):
        # Limit parallel scraping to avoid OOM
        self.semaphore = asyncio.Semaphore(max_concurrent)
        # Limit Tier 1 API concurrency to avoid hitting strict rate limits (429) across 15 chains
        self.tier1_semaphore = asyncio.Semaphore(3)

    async def _fetch_ankr(self, session, address: str, chain: str) -> list:
        # Map our internal chain names to Ankr's expected blockchain names
        ankr_chain_map = {
            "ETHEREUM": "eth",
            "BSC": "bsc",
            "POLYGON": "polygon",
            "ARBITRUM": "arbitrum",
            "BASE": "base",
            "OPTIMISM": "optimism",
            "AVALANCHE": "avalanche",
            "FANTOM": "fantom",
            "SYSCOIN": "syscoin",
            "LINEA": "linea"
        }
        ankr_chain = ankr_chain_map.get(chain)
        if not ankr_chain: return None

        ankr_key = api_rotator._get_api_key("ANKR") or os.environ.get("ANKR_API_KEY", "")
        if not ankr_key: return None
            
        url = f"https://rpc.ankr.com/multichain/{ankr_key}"
        all_txs = []
        page_token = ""
        
        retries = 0
        while True:
            payload = {
                "jsonrpc": "2.0",
                "method": "ankr_getTransactionsByAddress",
                "params": {
                    "blockchain": ankr_chain,
                    "address": address,
                    "descOrder": True
                },
                "id": 1
            }
            if page_token:
                payload["params"]["pageToken"] = page_token
                
            try:
                async with session.post(url, json=payload, timeout=15) as r:
                    if r.status == 429:
                        raise Exception(f"429")
                    if r.status != 200:
                        raise Exception(f"Ankr API Error on {chain}: {r.status}")
                        
                    data = await r.json()
                    if "error" in data:
                        raise Exception(f"Ankr API Error Payload on {chain}: {data['error']}")
                        
                    result = data.get("result", {})
                    txs = result.get("transactions", [])
                    
                    for tx in txs:
                        val = tx.get("value", "0")
                        if val.startswith("0x"): val = str(int(val, 16))
                        
                        all_txs.append({
                            "hash": tx.get("hash"),
                            "from": str(tx.get("from", "")).lower(),
                            "to": str(tx.get("to", "")).lower(),
                            "value": val,
                            "timeStamp": str(tx.get("timestamp", 0)),
                            "methodId": tx.get("input", "0x")[:10],
                            "contractAddress": str(tx.get("contractAddress", "")).lower()
                        })
                        
                    next_page = result.get("nextPageToken")
                    if not next_page or not txs:
                        break
                        
                    page_token = next_page
                    retries = 0 # reset on success
                    await asyncio.sleep(0.5)
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "Rate limit" in err_str) and retries < 3:
                    retries += 1
                    delay = 1.5 ** retries
                    logger.warning(f"Ankr 429 Rate Limit on {chain}. Retrying {retries}/3 in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"Ankr Request failed on {chain}: {e}")
                return None
        return all_txs

    async def _fetch_etherscan(self, session, address: str, chain: str) -> list:
        chain_map = {
            "ETHEREUM": ("https://api.etherscan.io/api", api_rotator._get_api_key("ETHERSCAN")),
            "BSC": ("https://api.bscscan.com/api", api_rotator._get_api_key("BSCSCAN")),
            "POLYGON": ("https://api.polygonscan.com/api", api_rotator._get_api_key("POLYGONSCAN")),
            "ARBITRUM": ("https://api.arbiscan.io/api", api_rotator._get_api_key("ARBISCAN")),
            "BASE": ("https://api.basescan.org/api", api_rotator._get_api_key("BASESCAN")),
            "OPTIMISM": ("https://api-optimistic.etherscan.io/api", api_rotator._get_api_key("OPTIMISMSCAN")),
            "CELO": ("https://api.celoscan.io/api", api_rotator._get_api_key("CELOSCAN")),
            "LINEA": ("https://api.lineascan.build/api", api_rotator._get_api_key("LINEASCAN")),
        }
        
        if chain not in chain_map: return None
        base_url, api_key = chain_map[chain]
        if not api_key: return None

        all_txs = []
        page = 1
        offset = 100
        retries = 0
        try:
            while True:
                params = {
                    "module": "account",
                    "action": "txlist",
                    "address": address,
                    "startblock": 0,
                    "endblock": 99999999,
                    "page": page,
                    "offset": offset,
                    "sort": "desc",
                    "apikey": api_key
                }
                async with session.get(base_url, params=params, timeout=15) as r:
                    if r.status == 429:
                        raise Exception("429")
                    if r.status != 200:
                        raise Exception(f"Etherscan Error on {chain}: {r.status}")
                    data = await r.json()
                    
                    if data.get("status") != "1" and "No transactions found" not in data.get("message", ""):
                        if data.get("message") == "NOTOK":
                            raise Exception("429 Rate limit (NOTOK)")
                        raise Exception(f"Etherscan API Error on {chain}: {data.get('message')}")
                        
                    txs = data.get("result", [])
                    if isinstance(txs, list):
                        for tx in txs:
                            all_txs.append({
                                "hash": tx.get("hash"),
                                "from": str(tx.get("from", "")).lower(),
                                "to": str(tx.get("to", "")).lower(),
                                "value": tx.get("value", "0"),
                                "timeStamp": tx.get("timeStamp", "0"),
                                "methodId": tx.get("methodId", "0x")[:10],
                                "contractAddress": str(tx.get("contractAddress", "")).lower()
                            })
                    
                    if not isinstance(txs, list) or len(txs) < offset:
                        break # End of pagination
                        
                    page += 1
                    retries = 0 # reset on success
                    await asyncio.sleep(0.3) # Rate limit protection
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "NOTOK" in err_str or "Rate limit" in err_str) and retries < 3:
                retries += 1
                delay = 1.5 ** retries
                logger.warning(f"Etherscan 429 Rate Limit on {chain}. Retrying {retries}/3 in {delay:.1f}s...")
                await asyncio.sleep(delay)
                # Restart the loop at the current page
            else:
                logger.error(f"Etherscan Request failed on {chain}: {e}")
                return None
        return all_txs
    async def _fetch_tatum(self, session, address: str, chain: str) -> list:
        tatum_chain_map = {
            "ETHEREUM": "ethereum",
            "BSC": "bsc",
            "POLYGON": "polygon",
            "CELO": "celo"
        }
        tatum_chain = tatum_chain_map.get(chain)
        if not tatum_chain: return None
        
        tatum_key = api_rotator._get_api_key("TATUM")
        if not tatum_key: return None

        all_txs = []
        retries = 0
        while retries <= 3:
            try:
                url = f"https://api.tatum.io/v3/{tatum_chain}/account/transaction/{address}"
                headers = {"x-api-key": tatum_key}
                
                async with session.get(url, headers=headers, timeout=15) as r:
                    if r.status in [429, 402]:
                        raise Exception(f"{r.status}")
                    if r.status != 200:
                        raise Exception(f"Tatum Error on {chain}: {r.status}")
                    txs = await r.json()
                    if isinstance(txs, list):
                        for tx in txs:
                            all_txs.append({
                                "hash": tx.get("hash"),
                                "from": str(tx.get("from", "")).lower(),
                                "to": str(tx.get("to", "")).lower(),
                                "value": str(tx.get("value", "0")),
                                "timeStamp": str(tx.get("timestamp", 0) // 1000) if tx.get("timestamp") else "0",
                                "methodId": tx.get("input", "0x")[:10],
                                "contractAddress": str(tx.get("contractAddress", "")).lower()
                            })
                    break # Success, exit retry loop
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "402" in err_str) and retries < 3:
                    retries += 1
                    delay = 1.5 ** retries
                    logger.warning(f"Tatum Rate/Payment Limit on {chain}. Retrying {retries}/3 in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Tatum Request failed on {chain}: {e}")
                    return None
        return all_txs

    async def _fetch_bitquery(self, session, address: str, chain: str) -> list:
        bitquery_chain_map = {
            "ETHEREUM": "ethereum",
            "BSC": "bsc",
            "POLYGON": "matic"
        }
        bq_chain = bitquery_chain_map.get(chain)
        if not bq_chain: return None

        bq_key = api_rotator._get_api_key("BITQUERY")
        if not bq_key: return None

        query = f"""
        {{
          ethereum(network: {bq_chain}) {{
            transactions(
              txSender: {{is: "{address}"}}
              options: {{desc: "block.timestamp.unixtime", limit: 1000}}
            ) {{
              hash
              sender {{ address }}
              to {{ address }}
              value
              block {{ timestamp {{ unixtime }} }}
            }}
            transfers(
              receiver: {{is: "{address}"}}
              options: {{desc: "block.timestamp.unixtime", limit: 1000}}
            ) {{
              transaction {{ hash }}
              sender {{ address }}
              receiver {{ address }}
              amount
              block {{ timestamp {{ unixtime }} }}
            }}
          }}
        }}
        """

        all_txs = []
        try:
            url = "https://graphql.bitquery.io"
            headers = {"X-API-KEY": bq_key}
            async with session.post(url, json={"query": query}, headers=headers, timeout=15) as r:
                if r.status != 200:
                    raise Exception(f"Bitquery Error on {chain}: {r.status}")
                data = await r.json()
                eth_data = data.get("data", {}).get("ethereum", {})
                
                for tx in eth_data.get("transactions", []):
                    all_txs.append({
                        "hash": tx.get("hash"),
                        "from": str(tx.get("sender", {}).get("address", "")).lower(),
                        "to": str(tx.get("to", {}).get("address", "")).lower(),
                        "value": str(tx.get("value", "0")),
                        "timeStamp": str(tx.get("block", {}).get("timestamp", {}).get("unixtime", 0)),
                        "methodId": "0x",
                        "contractAddress": ""
                    })
                    
                for tx in eth_data.get("transfers", []):
                    all_txs.append({
                        "hash": tx.get("transaction", {}).get("hash"),
                        "from": str(tx.get("sender", {}).get("address", "")).lower(),
                        "to": str(tx.get("receiver", {}).get("address", "")).lower(),
                        "value": str(tx.get("amount", "0")),
                        "timeStamp": str(tx.get("block", {}).get("timestamp", {}).get("unixtime", 0)),
                        "methodId": "0x",
                        "contractAddress": ""
                    })
        except Exception as e:
            logger.error(f"Bitquery Request failed on {chain}: {e}")
            return None
        return all_txs

    async def _fetch_tier1_api(self, session, address: str, chain: str) -> list:
        """Fallback Tier 1: Multi-Provider Rotation (Ankr, Etherscan, Tatum, Bitquery, etc.)"""
        chain = chain.upper()
        
        # TRON special handling
        if chain == "TRON":
            all_txs = []
            try:
                tron_url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20?limit=20"
                async with session.get(tron_url, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        txs = data.get("data", [])
                        for tx in txs:
                            all_txs.append({
                                "hash": tx.get("transaction_id"),
                                "from": str(tx.get("from", "")).lower(),
                                "to": str(tx.get("to", "")).lower(),
                                "value": tx.get("value", "0"),
                                "timeStamp": str(int(tx.get("block_timestamp", 0)) // 1000),
                                "contractAddress": str(tx.get("token_info", {}).get("address", "")).lower()
                            })
                tron_url_trx = f"https://api.trongrid.io/v1/accounts/{address}/transactions?limit=20"
                async with session.get(tron_url_trx, timeout=15) as r:
                    if r.status == 200:
                        data = await r.json()
                        txs = data.get("data", [])
                        for tx in txs:
                            raw = tx.get("raw_data", {}).get("contract", [{}])[0].get("parameter", {}).get("value", {})
                            val = str(raw.get("amount", 0))
                            if not val or val == "0": continue
                            all_txs.append({
                                "hash": tx.get("txID"),
                                "from": str(raw.get("owner_address", "")).lower(),
                                "to": str(raw.get("to_address", "")).lower(),
                                "value": val,
                                "timeStamp": str(int(tx.get("raw_data", {}).get("timestamp", 0)) // 1000)
                            })
                return all_txs
            except Exception as e:
                logger.error(f"TronGrid Request failed: {e}")
                return None

        # Tier 1 Providers in Rotation Order
        providers = [
            ("Etherscan", self._fetch_etherscan),
            ("Ankr", self._fetch_ankr),
            ("Tatum", self._fetch_tatum),
            ("Bitquery", self._fetch_bitquery)
        ]
        
        async with self.tier1_semaphore:
            for name, fetch_func in providers:
                txs = await fetch_func(session, address, chain)
                if txs is not None:
                    logger.info(f"[Swarm Agent] Extracted {len(txs)} historical TXs from Tier 1 ({name}) API for {address} on {chain}")
                    return txs
                
        return None

    async def _fetch_tier2_scraper(self, address: str, chain: str) -> list:
        """Fallback Tier 2: Deep DOM Headless Scraper with Pagination loops"""
        async with self.semaphore:
            logger.info(f"[Swarm Agent] Scraping {chain} for {address}...")
            return await scraper_instance.scrape_evm_explorer(address, chain) # Assuming it handles pagination internally or we augment it

    async def fetch_chain_data(self, session, address: str, chain: str, progress_callback=None) -> list:
        """Execute the fallback waterfall for a specific chain."""
        if progress_callback:
            await progress_callback(f"Scanning {chain} via Tier 1 APIs...")
        # Try API first
        txs = await self._fetch_tier1_api(session, address, chain)
        if txs is not None:
            if progress_callback:
                await progress_callback(f"Extracted {len(txs)} TXs from {chain} [API]")
            # API succeeded (even if 0 transactions were found)
            return txs
            
        # Fallback to Deep DOM Scraper for Entity Identity (Cannot scrape raw TXs easily via DOM)
        logger.warning(f"Tier 1 API failed for {address} on {chain}. Delegating to Swarm Headless Scraper (Tier 2)...")
        if progress_callback:
            await progress_callback(f"API failed on {chain}. Delegating to Headless Scraper...")
            
        label, cluster = await self._fetch_tier2_scraper(address, chain)
        if label or cluster:
            msg = f"Scraped identity via DOM on {chain}: {label} ({cluster})"
            logger.info(f"[Swarm Agent] {msg}")
            if progress_callback:
                await progress_callback(msg)
            
        # We must return an empty list of transactions to prevent NoneType errors in tracer
        return []

    async def swarm_fetch(self, session, address: str, chains: list, progress_callback=None) -> dict:
        """Parallel fetch across multiple chains using a swarm of workers."""
        logger.info(f"[*] Dispatching swarm agents for {address} across {len(chains)} chains...")
        if progress_callback:
            await progress_callback(f"Dispatching omni-chain swarm for {address[:8]}...")
            
        tasks = []
        for chain in chains:
            tasks.append(self.fetch_chain_data(session, address, chain, progress_callback))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated_data = {}
        for idx, chain in enumerate(chains):
            res = results[idx]
            if isinstance(res, Exception):
                logger.error(f"[Swarm Error] Agent failed on {chain}: {res}")
                aggregated_data[chain] = []
            else:
                aggregated_data[chain] = res
                
        return aggregated_data

# Singleton
swarm_instance = SwarmOrchestrator()
