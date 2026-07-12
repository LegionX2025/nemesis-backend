import logging
from datetime import datetime, timezone

logger = logging.getLogger("OmniChainEngine.Bridge")

class BridgeResolver:
    def __init__(self, db):
        self.db = db
        # If DB is None (no mongo yet), we use an in-memory fallback
        self.mock_db = []

    async def find_bridge_symmetry(self, edge: dict):
        """
        Takes a state_edge dict (MINT, BURN, LOCK, RELEASE) and tries to find its cross-chain counterpart.
        Returns the counterpart entity_id if found, else None.
        """
        if not self.db:
            return None
        
        try:
            links = self.db.bridge_links
            # Lookup based on the transaction hash
            tx_hash = edge.get("tx_hash")
            
            link = await links.find_one({
                "$or": [
                    {"mint_tx": tx_hash},
                    {"lock_tx": tx_hash},
                    {"burn_tx": tx_hash},
                    {"release_tx": tx_hash}
                ]
            })
            
            if link:
                # We found the bridge link. Now return the counterpart.
                if edge["edge_type"] in ["MINT", "RELEASE"]:
                    # We are looking at the destination, return the source
                    return link.get("source_entity")
                elif edge["edge_type"] in ["LOCK", "BURN"]:
                    # We are looking at the source, return the destination
                    return link.get("target_entity")
            return None
        except Exception as e:
            logger.error(f"Bridge symmetry error: {e}")
            return None

    async def register_bridge_link(self, source_chain, target_chain, lock_tx, mint_tx, asset_pair, source_entity, target_entity, bridge_entity):
        """
        Registers a verified bridge hop in the database.
        """
        if not self.db:
            return
            
        try:
            await self.db.bridge_links.update_one(
                {"lock_tx": lock_tx, "mint_tx": mint_tx},
                {"$set": {
                    "source_chain": source_chain,
                    "target_chain": target_chain,
                    "asset_pair": asset_pair,
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "bridge_entity": bridge_entity,
                    "timestamp": datetime.now(timezone.utc)
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Bridge registration error: {e}")
