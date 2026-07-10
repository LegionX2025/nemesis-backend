from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ------------------------------------------------------------------------------
# MONGODB ATLAS SCHEMAS (DOCUMENT STORE)
# ------------------------------------------------------------------------------

class TracerProfile(BaseModel):
    """Schema for a traced wallet address profile in NEMESIS TRACER"""
    address: str
    chain: str
    resolved_label: Optional[str] = None
    cluster_id: Optional[str] = None
    risk_score: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    transaction_count: int = 0
    total_volume_usd: float = 0.0
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NemesisID(BaseModel):
    """Schema for Entity Resolution and KYC correlations in NEMESIS ID"""
    entity_id: str
    entity_type: str # e.g. EXCHANGE, MIXER, PERSON, ORGANIZATION
    name: str
    aliases: List[str] = []
    associated_wallets: List[str] = []
    jurisdiction: Optional[str] = None
    osint_score: float = 0.0
    kyc_level: str = "UNKNOWN"
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DarknetRecord(BaseModel):
    """Schema for OSINT scraped marketplace addresses and hidden services"""
    onion_url: str
    service_name: str
    status: str # ACTIVE, SEIZED, OFFLINE
    category: str # e.g. MARKETPLACE, FORUM, MIXER
    extracted_wallets: List[str] = []
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0
    raw_content_hash: str

class EntityNode(BaseModel):
    id: str = Field(alias="_id")
    type: str # wallet|contract|program|exchange|bridge|nft|memo_id
    chain: str
    address: str
    labels: List[str] = []
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    cluster_id: Optional[str] = None

class NormalizedTransaction(BaseModel):
    id: str = Field(alias="_id")
    chain: str
    block_time: datetime
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    value: str
    raw: Dict[str, Any] = {}
    parsed: Dict[str, str] = {} # method, asset, amount

class StateEvent(BaseModel):
    id: str = Field(alias="_id")
    tx_hash: str
    chain: str
    event_type: str # Transfer|Mint|Burn|Swap|Deposit|Memo|Instruction
    signature: str
    source_entity: str
    target_entity: str
    asset: str
    amount: str
    metadata: Dict[str, str] = {}

class StateEdge(BaseModel):
    id: str = Field(alias="_id")
    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    edge_type: str # TRANSFER|MINT|BURN|LOCK|RELEASE|SWAP|BORROW|NFT_TRADE|BRIDGE_HOP|INTERNAL_LEDGER
    tx_hash: str
    chain: str
    asset: str
    amount: str
    confidence: float = 1.0
    timestamp: datetime

class BridgeLink(BaseModel):
    id: str = Field(alias="_id")
    source_chain: str
    target_chain: str
    lock_tx: str
    mint_tx: str
    asset_pair: List[str] = []
    time_delta_sec: int
    bridge_entity: str

class IdentityArtifact(BaseModel):
    id: str = Field(alias="_id")
    type: str # memo|tag|uid|topic
    value: str
    linked_entities: List[str] = []
    chain: str

# ------------------------------------------------------------------------------
# NEO4J GRAPH CYPHER QUERIES (GRAPH STORE)
# ------------------------------------------------------------------------------

class GraphSchemas:
    """Cypher query templates for Neo4j Knowledge Graph operations"""
    
    # 1. Node Creation
    MERGE_WALLET = """
    MERGE (w:Wallet {address: $address})
    ON CREATE SET w.chain = $chain, w.created_at = timestamp()
    ON MATCH SET w.last_seen = timestamp()
    RETURN w
    """
    
    MERGE_ENTITY = """
    MERGE (e:Entity {name: $name})
    ON CREATE SET e.type = $type, e.created_at = timestamp()
    RETURN e
    """
    
    MERGE_DARKNET_SERVICE = """
    MERGE (d:DarknetService {onion_url: $onion_url})
    ON CREATE SET d.name = $name, d.category = $category
    RETURN d
    """
    
    # 2. Edge Creation
    LINK_WALLET_TO_ENTITY = """
    MATCH (w:Wallet {address: $address})
    MATCH (e:Entity {name: $name})
    MERGE (w)-[r:BELONGS_TO]->(e)
    ON CREATE SET r.confidence = $confidence, r.timestamp = timestamp()
    RETURN r
    """
    
    LINK_WALLET_TRANSACTION = """
    MATCH (w1:Wallet {address: $from_address})
    MATCH (w2:Wallet {address: $to_address})
    MERGE (w1)-[r:TRANSACTED_WITH {tx_hash: $tx_hash}]->(w2)
    ON CREATE SET r.amount = $amount, r.asset = $asset, r.timestamp = $timestamp
    RETURN r
    """
    
    LINK_DARKNET_WALLET = """
    MATCH (d:DarknetService {onion_url: $onion_url})
    MATCH (w:Wallet {address: $address})
    MERGE (d)-[r:HOSTS_WALLET]->(w)
    ON CREATE SET r.scraped_at = timestamp()
    RETURN r
    """

    # 3. Analytics Queries
    FIND_SHORTEST_PATH = """
    MATCH (start:Wallet {address: $start_addr}), (end:Wallet {address: $end_addr})
    MATCH p = shortestPath((start)-[:TRANSACTED_WITH*..6]-(end))
    RETURN p
    """
    
    DETECT_MIXING_LOOPS = """
    MATCH (w:Wallet {address: $address})-[r1:TRANSACTED_WITH]->(mixer:Entity {type: 'MIXER'})
    MATCH (mixer)-[r2:TRANSACTED_WITH]->(w2:Wallet)
    MATCH (w2)-[r3:TRANSACTED_WITH]->(w3:Wallet)
    WHERE w = w3
    RETURN w, mixer, w2, w3
    """
