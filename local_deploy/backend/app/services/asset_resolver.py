import os
import json
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger("AssetResolver")

class AssetResolver:
    """
    Automated Asset Resolver
    Discovers, downloads, verifies, caches, and updates logos dynamically.
    Priority:
    1. Local Cache
    2. cryptologos.cc
    3. CoinGecko
    4. Trust Wallet
    5. DefiLlama
    6. CoinMarketCap
    7. TokenLists.org
    8. Chainlist
    9. WalletConnect / Explorer OpenGraph
    10. Official Website OpenGraph/Icon
    11. GitHub Organization
    12. Favicon Fallback
    """
    def __init__(self, static_dir="static/logos"):
        # We assume local_deploy directory is the working directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = os.path.join(base_dir, static_dir)
        os.makedirs(self.static_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.static_dir, "metadata.json")
        self.metadata = self._load_metadata()
        
        # In-memory caches for large datasets
        self._defillama_cache = None
        self._chainlist_cache = None
        self._tokenlists_cache = None

    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    async def _verify_and_download(self, session, url, filename):
        """Attempts to download an image from a URL. Returns the local path if successful."""
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "image" in content_type:
                        data = await response.read()
                        if len(data) > 100: # Verify it's not a tiny empty file
                            local_path = os.path.join(self.static_dir, filename)
                            with open(local_path, "wb") as f:
                                f.write(data)
                            return f"/static/logos/{filename}", url
        except Exception as e:
            pass
        return None, None

    async def _fetch_json(self, session, url):
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
        except:
            pass
        return None

    async def resolve(self, symbol: str, name: str = "", address: str = "", chain: str = "ethereum", website: str = "") -> dict:
        """
        Resolves the logo for a given asset following the priority list.
        """
        symbol_upper = symbol.upper()
        cache_key = f"{symbol_upper}_{chain}" if address else symbol_upper
        
        # 1. Check Local Cache
        if cache_key in self.metadata:
            return self.metadata[cache_key]

        name_clean = name.lower().replace(" ", "-") if name else ""
        symbol_clean = symbol.lower()
        filename = f"{symbol_clean}_{chain}.png" if address else f"{symbol_clean}.png"

        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            found_path = None
            found_source = None

            # 2. Cryptologos.cc
            if name_clean and symbol_clean and not found_path:
                url = f"https://cryptologos.cc/logos/{name_clean}-{symbol_clean}-logo.png"
                found_path, found_source = await self._verify_and_download(session, url, filename)

            # 3. CoinGecko
            if not found_path:
                cg_search = await self._fetch_json(session, f"https://api.coingecko.com/api/v3/search?query={symbol_clean}")
                if cg_search and "coins" in cg_search and len(cg_search["coins"]) > 0:
                    best_match = cg_search["coins"][0]
                    if best_match.get("large"):
                        found_path, found_source = await self._verify_and_download(session, best_match["large"], filename)

            # 4. Trust Wallet
            if not found_path:
                if address:
                    url = f"https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/{chain.lower()}/assets/{address}/logo.png"
                    found_path, found_source = await self._verify_and_download(session, url, filename)
                else:
                    url = f"https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/{chain.lower()}/info/logo.png"
                    found_path, found_source = await self._verify_and_download(session, url, filename)

            # 5. DefiLlama
            if not found_path:
                if not self._defillama_cache:
                    self._defillama_cache = await self._fetch_json(session, "https://api.llama.fi/protocols")
                if self._defillama_cache:
                    for p in self._defillama_cache:
                        if p.get("symbol", "").lower() == symbol_clean or p.get("name", "").lower() == name_clean:
                            if p.get("logo"):
                                found_path, found_source = await self._verify_and_download(session, p["logo"], filename)
                            break

            # 6. CoinMarketCap (Scrape Fallback)
            if not found_path and name_clean:
                try:
                    async with session.get(f"https://coinmarketcap.com/currencies/{name_clean}/", timeout=5) as r:
                        if r.status == 200:
                            html = await r.text()
                            soup = BeautifulSoup(html, "html.parser")
                            og_img = soup.find("meta", property="og:image")
                            if og_img and og_img.get("content"):
                                found_path, found_source = await self._verify_and_download(session, og_img["content"], filename)
                except:
                    pass

            # 7. TokenLists (Uniswap)
            if not found_path:
                if not self._tokenlists_cache:
                    self._tokenlists_cache = await self._fetch_json(session, "https://tokens.coingecko.com/uniswap/all.json")
                if self._tokenlists_cache and "tokens" in self._tokenlists_cache:
                    for t in self._tokenlists_cache["tokens"]:
                        if t.get("symbol", "").lower() == symbol_clean:
                            if t.get("logoURI"):
                                found_path, found_source = await self._verify_and_download(session, t["logoURI"], filename)
                            break

            # 8. Chainlist
            if not found_path:
                if not self._chainlist_cache:
                    self._chainlist_cache = await self._fetch_json(session, "https://chainid.network/chains.json")
                if self._chainlist_cache:
                    for c in self._chainlist_cache:
                        if c.get("nativeCurrency", {}).get("symbol", "").lower() == symbol_clean:
                            if c.get("icon"):
                                # If it's an IPFS hash, we'd need to resolve it, but we can try generic chainlist format
                                url = f"https://icons.llama.fi/chain/{name_clean}"
                                found_path, found_source = await self._verify_and_download(session, url, filename)
                            break

            # 9-10. Explorer / Official Website OpenGraph & Icons
            if not found_path and website:
                try:
                    async with session.get(website, timeout=5) as r:
                        if r.status == 200:
                            html = await r.text()
                            soup = BeautifulSoup(html, "html.parser")
                            og_img = soup.find("meta", property="og:image")
                            if og_img and og_img.get("content"):
                                found_path, found_source = await self._verify_and_download(session, og_img["content"], filename)
                            if not found_path:
                                icon = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
                                if icon and icon.get("href"):
                                    href = icon["href"]
                                    if not href.startswith("http"):
                                        parsed = urlparse(website)
                                        href = f"{parsed.scheme}://{parsed.netloc}/{href.lstrip('/')}"
                                    found_path, found_source = await self._verify_and_download(session, href, filename)
                except:
                    pass

            # 11. GitHub Org
            if not found_path and name_clean:
                url = f"https://avatars.githubusercontent.com/{name_clean}"
                found_path, found_source = await self._verify_and_download(session, url, filename)

            # 12. Favicon Fallback
            if not found_path and website:
                parsed = urlparse(website)
                domain = parsed.netloc or website
                url = f"https://s2.googleusercontent.com/s2/favicons?domain={domain}&sz=128"
                found_path, found_source = await self._verify_and_download(session, url, filename)

            # Finalize
            if found_path:
                asset_data = {
                    "name": name or symbol_upper,
                    "symbol": symbol_upper,
                    "logo": found_path,
                    "website": website,
                    "verified": True,
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": found_source
                }
            else:
                asset_data = {
                    "name": name or symbol_upper,
                    "symbol": symbol_upper,
                    "logo": "/static/images/default_token.png", # Fallback default
                    "website": website,
                    "verified": False,
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "None"
                }

            self.metadata[cache_key] = asset_data
            self._save_metadata()
            return asset_data

# Singleton instance to be used across the app
resolver_instance = AssetResolver()

async def resolve_asset_logo(symbol: str, name: str = "", address: str = "", chain: str = "ethereum", website: str = "") -> dict:
    return await resolver_instance.resolve(symbol, name, address, chain, website)
