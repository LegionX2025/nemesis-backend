import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("OmniChainEngine.GBEO")

class GBEOParser:
    def __init__(self):
        self.ontology_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gbeo_ontology.json")
        self.ontology = self._load_ontology()
        self.networks = self._build_network_map()

    def _load_ontology(self) -> dict:
        try:
            with open(self.ontology_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load GBEO Ontology: {e}")
            return {"families": {}}

    def _build_network_map(self) -> Dict[str, Any]:
        network_map = {}
        for family_id, family_data in self.ontology.get('families', {}).items():
            canonical_urls = family_data.get('canonical_urls', {})
            for net in family_data.get('networks', []):
                # Use chain overrides if defined, otherwise base URLs
                net_id = net['id'].upper()
                network_map[net_id] = {
                    'family': family_id,
                    'name': net.get('name'),
                    'base_url': net.get('base_url'),
                    'chain': net.get('chain', net_id.lower()), # For intelligence explorers
                    'canonical_urls': net.get('canonical_urls', canonical_urls) # Override if specific
                }
        return network_map

    def _format_url(self, template: str, params: dict) -> str:
        url = template
        for key, value in params.items():
            if value is not None:
                url = url.replace(f"{{{key}}}", str(value))
        return url

    def get_canonical_url(self, network: str, entity_type: str, **kwargs) -> Optional[str]:
        net = self.networks.get(network.upper())
        if not net:
            return None
            
        canonical_urls = net['canonical_urls']
        path_template = canonical_urls.get(entity_type)
        if not path_template:
            return None
            
        kwargs['chain'] = net.get('chain')
        path = self._format_url(path_template, kwargs)
        
        return f"{net['base_url']}{path}"

    def get_wallet_url(self, network: str, address: str) -> Optional[str]:
        return self.get_canonical_url(network, 'wallet', address=address)

    def get_transaction_url(self, network: str, txhash: str) -> Optional[str]:
        return self.get_canonical_url(network, 'transaction', txhash=txhash)

    def get_token_url(self, network: str, token: str) -> Optional[str]:
        return self.get_canonical_url(network, 'token', token=token)

    def get_event_logs_url(self, network: str, txhash: str) -> Optional[str]:
        return self.get_canonical_url(network, 'eventlog', txhash=txhash)
        
    def get_contract_source_url(self, network: str, address: str) -> Optional[str]:
        return self.get_canonical_url(network, 'contract_source', address=address)

    def get_supported_chains(self) -> list:
        return list(self.networks.keys())

    def get_explorer_name(self, network: str) -> str:
        net = self.networks.get(network.upper())
        if net:
            return f"{net.get('name')} Explorer"
        return "Unknown"
