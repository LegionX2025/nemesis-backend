import os
import json
import logging
import requests
import time
from urllib.parse import quote

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'asset_cache.json')

class AssetResolver:
    """
    Dynamically discovers, verifies, and caches official token and chain logos
    using a prioritized fallback list of public repositories.
    """
    
    def __init__(self):
        self.cache = self._load_cache()
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load asset cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save asset cache: {e}")

    def _check_url_exists(self, url):
        """Quick HEAD request to check if image exists"""
        try:
            r = requests.head(url, timeout=3)
            return r.status_code == 200
        except:
            return False

    def resolve(self, symbol, name=None, address=None, chain="ethereum"):
        """
        Attempts to resolve an asset. Priority:
        1. Local Cache
        2. CryptoLogos (for major coins)
        3. TrustWallet Assets (GitHub)
        4. Generic Fallback
        """
        symbol = symbol.upper()
        if not name:
            name = symbol

        cache_key = f"{chain}:{symbol}:{address or 'native'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        logger.info(f"Resolving asset: {symbol} ({name}) on {chain}...")

        # Sanitize for URLs
        url_name = name.lower().replace(" ", "-")
        url_symbol = symbol.lower()
        
        logo_url = None
        source = None

        # Priority 1: CryptoLogos
        cl_url = f"https://cryptologos.cc/logos/{url_name}-{url_symbol}-logo.png"
        if self._check_url_exists(cl_url):
            logo_url = cl_url
            source = "cryptologos.cc"

        # Priority 2: Trust Wallet (if we have a contract address)
        if not logo_url and address:
            # TrustWallet chains: ethereum, binance, tron, polygon, etc.
            tw_chain = chain.lower()
            if tw_chain == "bsc": tw_chain = "smartchain"
            # Trustwallet requires checksummed addresses for ETH/BSC, but we'll try raw for now
            tw_url = f"https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/{tw_chain}/assets/{address}/logo.png"
            if self._check_url_exists(tw_url):
                logo_url = tw_url
                source = "Trust Wallet Assets"

        # Priority 3: Fallback generic crypto icon via UI Avatars or CoinGecko search placeholder
        if not logo_url:
            logo_url = f"https://ui-avatars.com/api/?name={url_symbol}&background=random&rounded=true&font-size=0.4"
            source = "ui-avatars (Fallback)"

        result = {
            "name": name,
            "symbol": symbol,
            "logo": logo_url,
            "website": "",
            "verified": source != "ui-avatars (Fallback)",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source
        }

        self.cache[cache_key] = result
        self._save_cache()
        return result

    def bulk_resolve(self, assets_list):
        """
        assets_list = [{"symbol": "ETH", "name": "Ethereum", "chain": "ethereum"}, ...]
        """
        results = []
        for asset in assets_list:
            res = self.resolve(
                symbol=asset.get("symbol", "UNK"),
                name=asset.get("name"),
                address=asset.get("address"),
                chain=asset.get("chain", "ethereum")
            )
            results.append(res)
        return results

# Singleton instance for easy import
resolver = AssetResolver()
