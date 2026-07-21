import logging
from enum import Enum
from typing import List, Dict, Optional, Any, Union, Set
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger("NEMESIS_GBIO")

# ==============================================================================
# 1. CORE ENUMERATIONS (TAXONOMY & ONTOLOGY)
# ==============================================================================

class BlockchainNetwork(str, Enum):
    # EVM Ecosystem
    ETHEREUM = "ETHEREUM"
    BSC = "BSC"
    POLYGON = "POLYGON"
    AVALANCHE = "AVALANCHE"
    ARBITRUM = "ARBITRUM"
    OPTIMISM = "OPTIMISM"
    BASE = "BASE"
    LINEA = "LINEA"
    CELO = "CELO"
    FANTOM = "FANTOM"
    ZKSYNC = "ZKSYNC"
    BLAST = "BLAST"
    SCROLL = "SCROLL"
    MANTLE = "MANTLE"
    # UTXO & Privacy
    BITCOIN = "BITCOIN"
    LITECOIN = "LITECOIN"
    DOGECOIN = "DOGECOIN"
    BITCOIN_CASH = "BITCOIN_CASH"
    DASH = "DASH"
    ZCASH = "ZCASH"
    MONERO = "MONERO"
    # High-Performance / AltVM
    SOLANA = "SOLANA"
    TRON = "TRON"
    XRP = "XRP"
    STELLAR = "STELLAR"
    HEDERA = "HEDERA"
    CARDANO = "CARDANO"
    SUI = "SUI"
    APTOS = "APTOS"
    TON = "TON"
    NEAR = "NEAR"
    COSMOS = "COSMOS"
    INJECTIVE = "INJECTIVE"
    CELESTIA = "CELESTIA"
    KASPA = "KASPA"
    POLKADOT = "POLKADOT"
    UNKNOWN = "UNKNOWN"

class EntityClass(str, Enum):
    # Infrastructure & Users
    EOA_WALLET = "EOA_WALLET"
    SMART_CONTRACT = "SMART_CONTRACT"
    PROXY_CONTRACT = "PROXY_CONTRACT"
    MULTISIG = "MULTISIG"
    VALIDATOR = "VALIDATOR"
    MINING_POOL = "MINING_POOL"
    RELAYER = "RELAYER"
    # DeFi & Protocols
    DEX_ROUTER = "DEX_ROUTER"
    DEX_POOL = "DEX_POOL"
    LENDING_POOL = "LENDING_POOL"
    LIQUID_STAKING = "LIQUID_STAKING"
    YIELD_AGGREGATOR = "YIELD_AGGREGATOR"
    BRIDGE_ENDPOINT = "BRIDGE_ENDPOINT"
    BRIDGE_VAULT = "BRIDGE_VAULT"
    # Centralized Entities
    EXCHANGE_HOT = "EXCHANGE_HOT"
    EXCHANGE_COLD = "EXCHANGE_COLD"
    EXCHANGE_DEPOSIT = "EXCHANGE_DEPOSIT"
    OTC_BROKER = "OTC_BROKER"
    CUSTODIAN = "CUSTODIAN"
    PAYMENT_PROCESSOR = "PAYMENT_PROCESSOR"
    MERCHANT = "MERCHANT"
    # Obfuscation & Privacy
    MIXER_ROUTER = "MIXER_ROUTER"
    MIXER_POOL = "MIXER_POOL"
    COINJOIN_COORDINATOR = "COINJOIN_COORDINATOR"
    PRIVACY_POOL = "PRIVACY_POOL"
    # Threat Actors
    THREAT_ACTOR = "THREAT_ACTOR"
    SANCTIONED_ENTITY = "SANCTIONED_ENTITY"
    SCAM_OPERATOR = "SCAM_OPERATOR"
    EXPLOITER = "EXPLOITER"
    RANSOMWARE_AFFILIATE = "RANSOMWARE_AFFILIATE"
    # Governance & Communities
    DAO_TREASURY = "DAO_TREASURY"
    FOUNDATION = "FOUNDATION"
    UNKNOWN = "UNKNOWN"

class ThreatLevel(str, Enum):
    NONE = "NONE"           # Whitelisted, verified entities (e.g., Coinbase Hot Wallet)
    LOW = "LOW"             # Standard user activity, zero immediate threat exposure
    MEDIUM = "MEDIUM"       # DeFi heavy, P2P usage, interactions with unverified OTCs
    HIGH = "HIGH"           # Mixer exposure (1-hop), associated with known hacks, darknet proximity
    CRITICAL = "CRITICAL"   # Exploiter wallets, ransomware cash-out chains
    SEVERE = "SEVERE"       # OFAC Sanctioned Entities, State-sponsored APTs (Lazarus)

class TransferAction(str, Enum):
    """Normalized Semantic Edge Actions (GBIO Linkages)"""
    # 1. Base Value Transfers
    SENT_TO = "SENT_TO"
    RECEIVED_FROM = "RECEIVED_FROM"
    FEE_PAID_TO = "FEE_PAID_TO"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    AIRDROPPED_TO = "AIRDROPPED_TO"
    
    # 2. Asset Transformation
    WRAPPED_AS = "WRAPPED_AS"
    UNWRAPPED_TO = "UNWRAPPED_TO"
    MINTED = "MINTED"
    BURNED = "BURNED"
    PEGGED_TO = "PEGGED_TO"
    
    # 3. DeFi Operations
    SWAPPED_TO = "SWAPPED_TO"
    ADDED_LIQUIDITY = "ADDED_LIQUIDITY"
    REMOVED_LIQUIDITY = "REMOVED_LIQUIDITY"
    BORROWED = "BORROWED"
    REPAID = "REPAID"
    LIQUIDATED = "LIQUIDATED"
    FLASH_LOAN_TAKEN = "FLASH_LOAN_TAKEN"
    FLASH_LOAN_REPAID = "FLASH_LOAN_REPAID"
    STAKED = "STAKED"
    UNSTAKED = "UNSTAKED"
    REWARD_CLAIMED = "REWARD_CLAIMED"
    
    # 4. Cross-Chain & Bridging
    BRIDGED_TO = "BRIDGED_TO"
    BRIDGED_FROM = "BRIDGED_FROM"
    BRIDGE_LOCKED = "BRIDGE_LOCKED"
    BRIDGE_UNLOCKED = "BRIDGE_UNLOCKED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    VALIDATED_BY = "VALIDATED_BY"
    
    # 5. Obfuscation & AML
    MIXED_WITH = "MIXED_WITH"
    COINJOINED = "COINJOINED"
    PEELED_TO = "PEELED_TO"
    SHIELDED = "SHIELDED"
    UNSHIELDED = "UNSHIELDED"
    CONSOLIDATED_IN = "CONSOLIDATED_IN"
    
    # 6. Exchange & Custody
    DEPOSITED_TO = "DEPOSITED_TO"
    WITHDRAWN_FROM = "WITHDRAWN_FROM"
    SWEPT_TO = "SWEPT_TO"
    CASHED_OUT = "CASHED_OUT"
    
    # 7. NFTs
    MINTED_NFT = "MINTED_NFT"
    TRANSFERRED_NFT = "TRANSFERRED_NFT"
    LISTED_NFT = "LISTED_NFT"
    PURCHASED_NFT = "PURCHASED_NFT"
    
    # 8. Smart Contract Execution & MEV
    DEPLOYED_CONTRACT = "DEPLOYED_CONTRACT"
    CALLED_FUNCTION = "CALLED_FUNCTION"
    APPROVED_SPENDER = "APPROVED_SPENDER"
    REVOKED_SPENDER = "REVOKED_SPENDER"
    UPGRADED_PROXY = "UPGRADED_PROXY"
    EXECUTED_ARBITRAGE = "EXECUTED_ARBITRAGE"
    SANDWICHED = "SANDWICHED"
    BRIBED_MINER = "BRIBED_MINER"

class BehavioralIndicator(str, Enum):
    STRUCTURING = "STRUCTURING"           # Breaking down large transactions to avoid thresholds
    LAYERING = "LAYERING"                 # High velocity hops across multiple dummy wallets
    PEELING_CHAIN = "PEELING_CHAIN"       # Gradual siphoning of a large UTXO/Balance
    FAN_OUT = "FAN_OUT"                   # Distributing funds to many unique addresses (Dispersion)
    FAN_IN = "FAN_IN"                     # Consolidating funds from many unique addresses (Collection)
    RAPID_MOVEMENT = "RAPID_MOVEMENT"     # Assets moved immediately upon receipt (Bot behavior)
    DEX_LAUNDERING = "DEX_LAUNDERING"     # Rapid swaps across multiple tokens to break heuristics

class AMLFlag(str, Enum):
    OFAC_SANCTION_EXPOSURE = "OFAC_SANCTION_EXPOSURE"
    MIXER_EXPOSURE = "MIXER_EXPOSURE"
    DARKNET_EXPOSURE = "DARKNET_EXPOSURE"
    KNOWN_EXPLOIT_FUNDS = "KNOWN_EXPLOIT_FUNDS"
    HIGH_RISK_JURISDICTION = "HIGH_RISK_JURISDICTION"

# ==============================================================================
# 2. EVIDENTIARY DATA MODELS
# ==============================================================================

class EvidenceRecord(BaseModel):
    """
    Immutable cryptographic provenance for any ontology assertion.
    Never fabricated. Must point to verifiable on-chain or OSINT data.
    """
    source_provider: str = Field(..., description="e.g., Bitquery, Etherscan, Node_RPC, OSINT_Censys")
    retrieval_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    log_index: Optional[int] = None
    raw_payload: Optional[Union[Dict[str, Any], str]] = Field(None, description="Raw JSON or Hex from the provider")
    signature_matched: Optional[str] = Field(None, description="e.g., '0xa9059cbb' (transfer)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="1.0 for on-chain deterministic, <1.0 for heuristic")

    class Config:
        frozen = True # Evidence cannot be mutated once recorded

class ProtocolFingerprint(BaseModel):
    """Identity resolution for smart contracts and interacting services."""
    protocol_name: str
    category: str = Field(..., description="e.g., DEX, Bridge, Mixer")
    known_contracts: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    is_verified: bool = False

# ==============================================================================
# 3. KNOWLEDGE GRAPH MODELS (NODES & EDGES)
# ==============================================================================

class RiskProfile(BaseModel):
    """Calculated Risk Analytics for an Entity"""
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    threat_level: ThreatLevel = Field(default=ThreatLevel.NONE)
    aml_flags: List[AMLFlag] = Field(default_factory=list)
    behavioral_indicators: List[BehavioralIndicator] = Field(default_factory=list)
    sanctions_distance: int = Field(default=-1, description="-1 for none, 0 for direct hit, >0 for hops")
    mixer_distance: int = Field(default=-1, description="-1 for none, 0 for direct interaction, >0 for hops")

class GBIONode(BaseModel):
    """A distinct entity in the blockchain universe (Wallet, Contract, CEX)."""
    identifier: str = Field(..., description="Blockchain address or public key")
    network: BlockchainNetwork
    entity_class: EntityClass = Field(default=EntityClass.UNKNOWN)
    labels: List[str] = Field(default_factory=list)
    
    # Risk & Intelligence
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)
    
    # Attribution
    attributed_entity: Optional[str] = Field(None, description="e.g., 'Binance', 'Lazarus Group'")
    attribution_confidence: float = Field(default=0.0)
    protocol_fingerprint: Optional[ProtocolFingerprint] = None
    
    # Lifecycle Tracking
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    balance_usd_estimate: float = 0.0

    @property
    def global_id(self) -> str:
        """Universal identifier across all chains."""
        return f"{self.network.value}:{self.identifier.lower()}"

class GBIOEdge(BaseModel):
    """A semantic relationship or transfer event between two GBIONodes."""
    edge_id: str = Field(..., description="Unique ID, usually tx_hash:log_index")
    action: TransferAction
    source_node_id: str = Field(..., description="Global ID of source")
    target_node_id: str = Field(..., description="Global ID of target")
    
    # Financial Context
    asset_symbol: str = Field(default="UNKNOWN")
    asset_address: Optional[str] = None # Contract address of token, None if native
    amount_native: float = Field(default=0.0)
    amount_usd_estimate: float = Field(default=0.0)
    
    # Provenance
    timestamp: datetime
    evidence: EvidenceRecord
    
    # Heuristic Context
    is_terminal_hop: bool = Field(default=False, description="True if landing at CEX/Mixer/Bridge")
    
    @validator('amount_native', 'amount_usd_estimate', pre=True)
    def validate_amounts(cls, v):
        try:
            val = float(v)
            return max(0.0, val) # No negative values
        except:
            return 0.0

# ==============================================================================
# 4. ONTOLOGY & FORENSIC ENGINE SERVICE
# ==============================================================================

class GBIOEngine:
    """
    Production-Grade Engine for creating, validating, and extracting graph intelligence.
    Implements deterministic topology analysis and AML risk scoring.
    """
    
    @staticmethod
    def construct_edge(
        action: TransferAction,
        source: GBIONode,
        target: GBIONode,
        asset: str,
        amount: float,
        usd_value: float,
        evidence: EvidenceRecord,
        timestamp: datetime
    ) -> GBIOEdge:
        """Factory method enforcing strict semantic consistency before edge creation."""
        
        # 1. Enforcement: CEX Deposit Rules
        if action == TransferAction.DEPOSITED_TO and target.entity_class not in [
            EntityClass.EXCHANGE_HOT, EntityClass.EXCHANGE_COLD, EntityClass.EXCHANGE_DEPOSIT, EntityClass.CUSTODIAN, EntityClass.OTC_BROKER
        ]:
            target.entity_class = EntityClass.EXCHANGE_DEPOSIT

        # 2. Enforcement: Mixer Interaction Rules
        if action == TransferAction.MIXED_WITH and target.entity_class not in [
            EntityClass.MIXER_POOL, EntityClass.MIXER_ROUTER, EntityClass.COINJOIN_COORDINATOR, EntityClass.PRIVACY_POOL
        ]:
            target.entity_class = EntityClass.MIXER_ROUTER
            target.risk_profile.threat_level = ThreatLevel.CRITICAL
            if AMLFlag.MIXER_EXPOSURE not in target.risk_profile.aml_flags:
                target.risk_profile.aml_flags.append(AMLFlag.MIXER_EXPOSURE)

        # 3. Enforcement: Bridge Routing Rules
        if action in [TransferAction.BRIDGED_TO, TransferAction.BRIDGE_LOCKED] and target.entity_class not in [
            EntityClass.BRIDGE_ENDPOINT, EntityClass.BRIDGE_VAULT
        ]:
            target.entity_class = EntityClass.BRIDGE_ENDPOINT

        return GBIOEdge(
            edge_id=f"{evidence.transaction_hash}:{evidence.log_index or 0}",
            action=action,
            source_node_id=source.global_id,
            target_node_id=target.global_id,
            asset_symbol=asset,
            amount_native=amount,
            amount_usd_estimate=usd_value,
            timestamp=timestamp,
            evidence=evidence,
            is_terminal_hop=action in [
                TransferAction.DEPOSITED_TO, TransferAction.BRIDGED_TO, TransferAction.MIXED_WITH, TransferAction.CASHED_OUT
            ]
        )

    @staticmethod
    def infer_node_class_from_behavior(target_node_id: str, edges: List[GBIOEdge]) -> EntityClass:
        """
        Production Heuristic Topology Analysis.
        Determines the organizational role of a wallet based solely on its graph interactions.
        """
        if not edges:
            return EntityClass.UNKNOWN

        relevant_edges = [e for e in edges if e.source_node_id == target_node_id or e.target_node_id == target_node_id]
        if not relevant_edges:
            return EntityClass.UNKNOWN

        in_edges = [e for e in relevant_edges if e.target_node_id == target_node_id]
        out_edges = [e for e in relevant_edges if e.source_node_id == target_node_id]
        
        in_degree = len(in_edges)
        out_degree = len(out_edges)
        unique_senders = len(set([e.source_node_id for e in in_edges]))
        unique_receivers = len(set([e.target_node_id for e in out_edges]))

        actions = [e.action for e in relevant_edges]
        action_counts = Counter(actions)

        # 1. Hot Wallet / Custodian Heuristic (High fan-in from diverse addresses, massive outgoing sweeps)
        if unique_senders > 500 and unique_receivers > 100:
            if action_counts.get(TransferAction.SWEPT_TO, 0) > 0 or action_counts.get(TransferAction.INTERNAL_TRANSFER, 0) > 50:
                return EntityClass.EXCHANGE_HOT

        # 2. Exchange Deposit Wallet Heuristic (Many deposits from 1 user, immediately swept to 1 hot wallet)
        if in_degree > 0 and out_degree > 0:
            if unique_receivers == 1 and unique_senders < 10:
                return EntityClass.EXCHANGE_DEPOSIT

        # 3. DEX Router Heuristic (Massive volume of SWAPPED_TO actions)
        if action_counts.get(TransferAction.SWAPPED_TO, 0) > (len(relevant_edges) * 0.7):
            return EntityClass.DEX_ROUTER

        # 4. Bridge Endpoint Heuristic
        if action_counts.get(TransferAction.BRIDGED_TO, 0) > 0 or action_counts.get(TransferAction.BRIDGE_LOCKED, 0) > 0:
            return EntityClass.BRIDGE_ENDPOINT

        # 5. Mining Pool Heuristic (Massive out-degree, primarily MINTED or Coinbase transactions)
        if action_counts.get(TransferAction.MINTED, 0) > 0 and unique_receivers > 500 and in_degree < 5:
            return EntityClass.MINING_POOL

        return EntityClass.EOA_WALLET

    @staticmethod
    def detect_behavioral_patterns(target_node_id: str, edges: List[GBIOEdge]) -> List[BehavioralIndicator]:
        """
        Forensic rule engine to identify obfuscation patterns in transaction sequences.
        """
        indicators = set()
        
        out_edges = sorted([e for e in edges if e.source_node_id == target_node_id], key=lambda x: x.timestamp)
        in_edges = sorted([e for e in edges if e.target_node_id == target_node_id], key=lambda x: x.timestamp)
        
        # 1. Fan-Out (Dispersion)
        unique_receivers = len(set([e.target_node_id for e in out_edges]))
        if len(out_edges) > 10 and unique_receivers > (len(out_edges) * 0.8):
            indicators.add(BehavioralIndicator.FAN_OUT)

        # 2. Fan-In (Consolidation)
        unique_senders = len(set([e.source_node_id for e in in_edges]))
        if len(in_edges) > 10 and unique_senders > (len(in_edges) * 0.8):
            indicators.add(BehavioralIndicator.FAN_IN)

        # 3. Rapid Movement (Bot/Script behavior)
        if in_edges and out_edges:
            for in_e in in_edges:
                for out_e in out_edges:
                    if out_e.timestamp >= in_e.timestamp:
                        time_diff = (out_e.timestamp - in_e.timestamp).total_seconds()
                        if 0 <= time_diff <= 30: # Moved within 30 seconds
                            indicators.add(BehavioralIndicator.RAPID_MOVEMENT)
                            break

        # 4. Peeling Chain
        if len(in_edges) == 1 and len(out_edges) > 5:
            in_val = in_edges[0].amount_usd_estimate
            if in_val > 10000: 
                avg_out = sum(e.amount_usd_estimate for e in out_edges) / len(out_edges)
                if avg_out < (in_val * 0.2): 
                    indicators.add(BehavioralIndicator.PEELING_CHAIN)

        # 5. DEX Laundering
        dex_actions = [e for e in out_edges if e.action == TransferAction.SWAPPED_TO]
        if len(dex_actions) >= 3:
            unique_assets = len(set([e.asset_symbol for e in dex_actions]))
            if unique_assets > 2:
                indicators.add(BehavioralIndicator.DEX_LAUNDERING)

        return list(indicators)

    @staticmethod
    def compute_aml_risk_profile(node: GBIONode, edges: List[GBIOEdge]) -> RiskProfile:
        """
        Enterprise AML Risk Computation Engine.
        Generates a 0-100 score based on topological exposure and threat flags.
        """
        profile = node.risk_profile
        base_score = 10.0 # Base operational risk
        
        # 1. Evaluate Direct Entity Threat Level
        if profile.threat_level == ThreatLevel.SEVERE:
            profile.overall_score = 100.0
            if AMLFlag.OFAC_SANCTION_EXPOSURE not in profile.aml_flags:
                profile.aml_flags.append(AMLFlag.OFAC_SANCTION_EXPOSURE)
            return profile
        elif profile.threat_level == ThreatLevel.CRITICAL:
            base_score += 75.0
        elif profile.threat_level == ThreatLevel.HIGH:
            base_score += 50.0

        # 2. Evaluate Graph/Edge Exposure
        relevant_edges = [e for e in edges if e.source_node_id == node.global_id or e.target_node_id == node.global_id]
        has_mixer_hop = False

        for edge in relevant_edges:
            if edge.action in [TransferAction.MIXED_WITH, TransferAction.COINJOINED, TransferAction.SHIELDED]:
                has_mixer_hop = True
            
            if AMLFlag.KNOWN_EXPLOIT_FUNDS in profile.aml_flags:
                base_score += 60.0

        if has_mixer_hop:
            base_score += 45.0
            profile.mixer_distance = 1 
            if AMLFlag.MIXER_EXPOSURE not in profile.aml_flags:
                profile.aml_flags.append(AMLFlag.MIXER_EXPOSURE)
                
        # 3. Behavioral Modifiers
        behaviors = GBIOEngine.detect_behavioral_patterns(node.global_id, edges)
        profile.behavioral_indicators = behaviors
        
        if BehavioralIndicator.PEELING_CHAIN in behaviors: base_score += 25.0
        if BehavioralIndicator.DEX_LAUNDERING in behaviors: base_score += 30.0
        if BehavioralIndicator.RAPID_MOVEMENT in behaviors: base_score += 15.0

        profile.overall_score = min(100.0, float(base_score))
        
        if profile.threat_level in [ThreatLevel.NONE, ThreatLevel.LOW, ThreatLevel.UNKNOWN]:
            if profile.overall_score >= 85.0: profile.threat_level = ThreatLevel.CRITICAL
            elif profile.overall_score >= 60.0: profile.threat_level = ThreatLevel.HIGH
            elif profile.overall_score >= 30.0: profile.threat_level = ThreatLevel.MEDIUM
            else: profile.threat_level = ThreatLevel.LOW

        return profile

# Provide a mock normalizer for the transition if it isn't fully built
class GBIONormalizer:
    @staticmethod
    def normalize_entity(target_entity, chain, raw_lbl, is_contract):
        # Basic mock wrapper during migration
        class MockObj:
            def __init__(self, e, l, c):
                self.entity_class = EntityClass.EXCHANGE_DEPOSIT if "EXCHANGE" in l else EntityClass.EOA_WALLET
                self.label = l
                self.threat_level = ThreatLevel.LOW
        return MockObj(target_entity, raw_lbl, is_contract)
