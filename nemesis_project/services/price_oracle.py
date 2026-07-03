import aiohttp
import asyncio
import logging
import time

logger = logging.getLogger("OmniChainEngine.PriceOracle")

# Map our internal chain names to DefiLlama chain prefixes
CHAIN_TO_LLAMA = {
    "ETHEREUM": "ethereum",
    "BSC": "bsc",
    "POLYGON": "polygon",
    "ARBITRUM": "arbitrum",
    "OPTIMISM": "optimism",
    "BASE": "base",
    "AVALANCHE": "avax",
    "FANTOM": "fantom",
    "CRONOS": "cronos",
    "SOLANA": "solana",
    "TRON": "tron",
    "BITCOIN": "bitcoin"
}

# Cache to avoid hammering DefiLlama
# Format: {(chain, token_address, timestamp_hour): price}
PRICE_CACHE = {}

async def _fetch_price_from_llama(url: str, coins: str) -> float:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5.0) as response:
                if response.status == 200:
                    data = await response.json()
                    coins_data = data.get("coins", {})
                    if coins in coins_data:
                        return float(coins_data[coins].get("price", 0.0))
                else:
                    logger.warning(f"DefiLlama API error {response.status}: {url}")
    except Exception as e:
        logger.error(f"Error fetching price from DefiLlama for {coins}: {e}")
    return 0.0

def get_llama_coin_id(chain: str, token_address: str) -> str:
    """ Convert our chain and token address to DefiLlama format. """
    chain_upper = chain.upper()
    llama_chain = CHAIN_TO_LLAMA.get(chain_upper)
    
    # If no token address (native asset) or 'native', map to coingecko ID if known
    if not token_address or token_address.lower() in ["native", "0x0000000000000000000000000000000000000000", "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"]:
        if chain_upper == "ETHEREUM": return "coingecko:ethereum"
        if chain_upper == "BITCOIN": return "coingecko:bitcoin"
        if chain_upper == "SOLANA": return "coingecko:solana"
        if chain_upper == "TRON": return "coingecko:tron"
        if chain_upper == "POLYGON": return "coingecko:matic-network"
        if chain_upper == "BSC": return "coingecko:binancecoin"
        if chain_upper == "AVALANCHE": return "coingecko:avalanche-2"
        # Fallback to chain native if supported by Llama
        if llama_chain:
            return f"{llama_chain}:0x0000000000000000000000000000000000000000"
    
    if llama_chain:
        return f"{llama_chain}:{token_address}"
        
    return ""

async def get_historical_usd_value(chain: str, token_address: str, amount: float, timestamp: int) -> float:
    """ Get the USD value of an amount of tokens at a specific historical timestamp. """
    if amount == 0: return 0.0
    
    coins = get_llama_coin_id(chain, token_address)
    if not coins:
        logger.warning(f"Could not map {chain}:{token_address} to DefiLlama format.")
        return 0.0
        
    # Round timestamp to the nearest hour for caching
    ts_hour = timestamp - (timestamp % 3600)
    cache_key = (chain, token_address, ts_hour)
    
    if cache_key in PRICE_CACHE:
        price = PRICE_CACHE[cache_key]
        return price * amount

    url = f"https://coins.llama.fi/prices/historical/{timestamp}/{coins}"
    price = await _fetch_price_from_llama(url, coins)
    
    if price > 0:
        PRICE_CACHE[cache_key] = price
        return price * amount
        
    return 0.0

async def get_current_usd_value(chain: str, token_address: str, amount: float) -> float:
    """ Get the current USD value of an amount of tokens. """
    if amount == 0: return 0.0
    
    coins = get_llama_coin_id(chain, token_address)
    if not coins:
        return 0.0
        
    # For current prices, cache for 5 minutes
    ts_5min = int(time.time()) - (int(time.time()) % 300)
    cache_key = (chain, token_address, "current", ts_5min)
    
    if cache_key in PRICE_CACHE:
        price = PRICE_CACHE[cache_key]
        return price * amount
        
    url = f"https://coins.llama.fi/prices/current/{coins}"
    price = await _fetch_price_from_llama(url, coins)
    
    if price > 0:
        PRICE_CACHE[cache_key] = price
        return price * amount
        
    return 0.0
