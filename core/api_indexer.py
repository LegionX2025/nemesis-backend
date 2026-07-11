import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load env in case it's not loaded by the parent process
load_dotenv()

logger = logging.getLogger("NEMESIS.v33.APIIndexer")

class APIEndpointIndexer:
    """
    Dynamically indexes API providers from the environment variables and constructs
    standardized endpoint configurations and authentication headers.
    """
    
    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {}
        self._index_providers()
        
    def _index_providers(self):
        """Scans the environment and indexes available providers."""
        logger.info("[API INDEXER] Initializing Dynamic Provider Index...")
        
        # 1. Multi-Chain Aggregators
        self._register_bitquery()
        self._register_tatum()
        self._register_oklink()
        
        # 2. Blockchain Ledger Scanners (Etherscan & Clones)
        self._register_etherscan_clones()
        
        # 3. RPC Node Providers
        self._register_infura()
        self._register_getblock()
        self._register_ankr()
        
        logger.info(f"[API INDEXER] Successfully indexed {len(self.providers)} providers.")

    def get_provider(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the configuration for a specific provider, if configured."""
        provider = self.providers.get(name.lower())
        if not provider:
            logger.warning(f"[API INDEXER] Provider '{name}' not found or missing credentials.")
        return provider

    def list_providers(self) -> Dict[str, str]:
        """Returns a simplified dict mapping provider name to auth_type."""
        return {name: cfg["auth_type"] for name, cfg in self.providers.items()}

    # -------------------------------------------------------------------------
    # Provider-Specific Registration Logic
    # -------------------------------------------------------------------------

    def _register_bitquery(self):
        token_v2 = os.getenv("BITQUERY_APIV2_TOKEN") or os.getenv("VITE_BITQUERY_APIV2_TOKEN")
        token_v1 = os.getenv("BITQUERY_API_TOKEN") or os.getenv("VITE_BITQUERY_API_TOKEN")
        
        # Prefer V2 token over V1
        token = token_v2 or token_v1
        
        if token:
            self.providers["bitquery"] = {
                "name": "Bitquery GraphQL V2",
                "type": "multi-chain-aggregator",
                "base_url": "https://graphql.bitquery.io",
                "auth_type": "bearer",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                "params": {}
            }

    def _register_tatum(self):
        key = os.getenv("TATUM_API_KEY")
        if key:
            self.providers["tatum"] = {
                "name": "Tatum Multi-Chain",
                "type": "multi-chain-aggregator",
                "base_url": "https://api.tatum.io/v3",
                "auth_type": "header",
                "headers": {
                    "x-api-key": key
                },
                "params": {}
            }
            
    def _register_oklink(self):
        key = os.getenv("OKLINK_API_KEY")
        if key and "NOT_REQUIRED" not in key:
            self.providers["oklink"] = {
                "name": "OKLink Intelligence",
                "type": "multi-chain-aggregator",
                "base_url": "https://www.oklink.com/api/v5",
                "auth_type": "header",
                "headers": {
                    "Ok-Access-Key": key
                },
                "params": {}
            }

    def _register_etherscan_clones(self):
        scanners = {
            "etherscan": ("ETHERSCAN_API_KEY", "https://api.etherscan.io/api"),
            "bscscan": ("BSCSCAN_API_KEY", "https://api.bscscan.com/api"),
            "polygonscan": ("POLYGONSCAN_API_KEY", "https://api.polygonscan.com/api"),
            "snowtrace": ("SNOWTRACE_API_KEY", "https://api.snowtrace.io/api"),
            "arbiscan": ("ARBISCAN_API_KEY", "https://api.arbiscan.io/api"),
            "optimism": ("OPTIMISMSCAN_API_KEY", "https://api-optimistic.etherscan.io/api"),
            "basescan": ("BASESCAN_API_KEY", "https://api.basescan.org/api")
        }
        
        for name, (env_key, url) in scanners.items():
            key = os.getenv(env_key)
            if key:
                self.providers[name] = {
                    "name": name.capitalize(),
                    "type": "ledger-scanner",
                    "base_url": url,
                    "auth_type": "query",
                    "headers": {},
                    "params": {
                        "apikey": key
                    }
                }

    def _register_infura(self):
        key = os.getenv("INFURA_API_KEY")
        if key:
            self.providers["infura"] = {
                "name": "Infura RPC",
                "type": "rpc-provider",
                "base_url": f"https://mainnet.infura.io/v3/{key}",
                "auth_type": "url",
                "headers": {},
                "params": {}
            }

    def _register_getblock(self):
        # Taking ETH as standard example
        key = os.getenv("GETBLOCK_ETH_KEY")
        if key:
            self.providers["getblock"] = {
                "name": "GetBlock RPC",
                "type": "rpc-provider",
                "base_url": f"https://go.getblock.io/{key}",
                "auth_type": "url",
                "headers": {},
                "params": {}
            }

    def _register_ankr(self):
        key = os.getenv("ANKR_API_KEY")
        if key:
            self.providers["ankr"] = {
                "name": "Ankr Multi-Chain RPC",
                "type": "rpc-provider",
                "base_url": f"https://rpc.ankr.com/multichain/{key}",
                "auth_type": "url",
                "headers": {},
                "params": {}
            }
