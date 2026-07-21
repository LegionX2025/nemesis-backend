from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ==============================================================================
# NEMESIS TRACER MODELS
# ==============================================================================

class TransactionNode(BaseModel):
    hash: str
    from_address: str
    to_address: str
    value: float
    asset: str
    timestamp: datetime
    chain: str
    risk_score: Optional[float] = 0.0

class WalletEntity(BaseModel):
    address: str
    chain: str
    label: str = "Unknown"
    classification: str = "Unknown" # e.g. Exchange, Mixer, Contract
    balance: Optional[float] = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    risk_score: float = 0.0

class TraceSession(BaseModel):
    trace_id: str
    target_addresses: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "In Progress"
    total_value_traced: float = 0.0
    wallets_discovered: int = 0
    transactions_analyzed: int = 0

# ==============================================================================
# NEMESIS ID MODELS
# ==============================================================================

class OSINTOccurrence(BaseModel):
    source: str # e.g. Twitter, Reddit, Pastebin, OKLink
    url: Optional[str] = None
    content_snippet: str
    confidence_score: float
    timestamp: datetime

class Fingerprint(BaseModel):
    ip_addresses: List[str] = Field(default_factory=list)
    device_hashes: List[str] = Field(default_factory=list)
    browser_agents: List[str] = Field(default_factory=list)

class SuspectProfile(BaseModel):
    profile_id: str
    name_alias: str
    associated_wallets: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    handles: List[str] = Field(default_factory=list)
    fingerprints: Optional[Fingerprint] = None
    occurrences: List[OSINTOccurrence] = Field(default_factory=list)

# ==============================================================================
# DARKNET MODELS
# ==============================================================================

class MixerInteraction(BaseModel):
    mixer_name: str
    deposit_address: str
    amount: float
    timestamp: datetime
    peel_chain_detected: bool = False

class DarknetVendor(BaseModel):
    vendor_id: str
    market_name: str
    pgp_key: Optional[str] = None
    associated_wallets: List[str] = Field(default_factory=list)
    mixer_interactions: List[MixerInteraction] = Field(default_factory=list)

class SanctionedEntity(BaseModel):
    entity_name: str
    sanctioning_body: str # e.g. OFAC
    wallets: List[str] = Field(default_factory=list)
    date_added: datetime

# ==============================================================================
# MACHINE LEARNING CLUSTERING MODELS
# ==============================================================================

class BehavioralPattern(BaseModel):
    pattern_name: str
    description: str
    confidence: float
    matching_transactions: List[str] = Field(default_factory=list)

class HeuristicRule(BaseModel):
    rule_id: str
    description: str
    weight: float

class ClusterGroup(BaseModel):
    cluster_id: str
    primary_entity_label: str
    wallets: List[str] = Field(default_factory=list)
    total_volume: float = 0.0
    behavioral_patterns: List[BehavioralPattern] = Field(default_factory=list)
    ml_confidence_score: float = 0.0
