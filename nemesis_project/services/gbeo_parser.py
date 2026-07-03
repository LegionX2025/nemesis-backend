import os
import json
import logging

logger = logging.getLogger("OmniChainEngine.GBEO")

class GBEOParser:
    def __init__(self):
        self.ontology_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gbeo_ontology.json")
        self.ontology = self._load_ontology()
        self.networks = {net['id'].upper(): net for net in self.ontology.get('networks', [])}

    def _load_ontology(self):
        try:
            with open(self.ontology_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load GBEO Ontology: {e}")
            return {"networks": []}

    def get_canonical_url(self, network: str, entity_type: str, value: str, block=None, token_id=None):
        """
        entity_type: 'wallet', 'transaction', 'token', 'nft', 'block', 'contract_source'
        """
        net = self.networks.get(network.upper())
        if not net:
            return None
            
        explorer = net.get('explorer', {})
        base_url = explorer.get('base_url', '')
        canonical_urls = explorer.get('canonical_urls', {})
        
        path_template = canonical_urls.get(entity_type)
        if not path_template:
            return None
            
        # Replace tokens
        path = path_template.replace('{address}', value).replace('{txhash}', value).replace('{token}', value)
        if block is not None:
            path = path.replace('{block}', str(block))
        if token_id is not None:
            path = path.replace('{tokenId}', str(token_id)).replace('{contract}', value)
            
        return f"{base_url}{path}"

    def get_explorer_name(self, network: str):
        net = self.networks.get(network.upper())
        if net:
            return net.get('explorer', {}).get('name', 'Unknown')
        return 'Unknown'
        
    def is_auto_ingest(self, network: str):
        net = self.networks.get(network.upper())
        if net:
            return net.get('explorer', {}).get('auto_ingest', False)
        return False
        
    def get_supported_chains(self):
        return [net['id'].upper() for net in self.ontology.get('networks', [])]
