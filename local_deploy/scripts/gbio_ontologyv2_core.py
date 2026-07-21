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
    NONE = "NONE"           
    LOW = "LOW"             
    MEDIUM = "MEDIUM"       
    HIGH = "HIGH"           
    CRITICAL = "CRITICAL"   
    SEVERE = "SEVERE"       

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
    STRUCTURING = "STRUCTURING"           
    LAYERING = "LAYERING"                 
    PEELING_CHAIN = "PEELING_CHAIN"       
    FAN_OUT = "FAN_OUT"                   
    FAN_IN = "FAN_IN"                     
    RAPID_MOVEMENT = "RAPID_MOVEMENT"     
    DEX_LAUNDERING = "DEX_LAUNDERING"     

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
    source_provider: str = Field(..., description="e.g., Bitquery, Etherscan, Node_RPC, OSINT_Censys")
    retrieval_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    log_index: Optional[int] = None
    raw_payload: Optional[Union[Dict[str, Any], str]] = Field(None, description="Raw JSON or Hex from the provider")
    signature_matched: Optional[str] = Field(None, description="e.g., '0xa9059cbb' (transfer)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="1.0 for on-chain deterministic, <1.0 for heuristic")

    class Config:
        frozen = True

class ProtocolFingerprint(BaseModel):
    protocol_name: str
    category: str = Field(..., description="e.g., DEX, Bridge, Mixer")
    known_contracts: List[str] = Field(default_factory=list)
    version: Optional[str] = None
    is_verified: bool = False

# ==============================================================================
# 3. KNOWLEDGE GRAPH MODELS (NODES & EDGES)
# ==============================================================================

class RiskProfile(BaseModel):
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    threat_level: ThreatLevel = Field(default=ThreatLevel.NONE)
    aml_flags: List[AMLFlag] = Field(default_factory=list)
    behavioral_indicators: List[BehavioralIndicator] = Field(default_factory=list)
    sanctions_distance: int = Field(default=-1, description="-1 for none, 0 for direct hit, >0 for hops")
    mixer_distance: int = Field(default=-1, description="-1 for none, 0 for direct interaction, >0 for hops")

class GBIONode(BaseModel):
    identifier: str = Field(..., description="Blockchain address or public key")
    network: BlockchainNetwork
    entity_class: EntityClass = Field(default=EntityClass.UNKNOWN)
    labels: List[str] = Field(default_factory=list)
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)
    attributed_entity: Optional[str] = Field(None)
    attribution_confidence: float = Field(default=0.0)
    protocol_fingerprint: Optional[ProtocolFingerprint] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    balance_usd_estimate: float = 0.0

    @property
    def global_id(self) -> str:
        return f"{self.network.value}:{self.identifier.lower()}"

class GBIOEdge(BaseModel):
    edge_id: str = Field(..., description="Unique ID, usually tx_hash:log_index")
    action: TransferAction
    source_node_id: str = Field(..., description="Global ID of source")
    target_node_id: str = Field(..., description="Global ID of target")
    asset_symbol: str = Field(default="UNKNOWN")
    asset_address: Optional[str] = None 
    amount_native: float = Field(default=0.0)
    amount_usd_estimate: float = Field(default=0.0)
    timestamp: datetime
    evidence: EvidenceRecord
    is_terminal_hop: bool = Field(default=False)
    
    @validator('amount_native', 'amount_usd_estimate', pre=True)
    def validate_amounts(cls, v):
        try:
            val = float(v)
            return max(0.0, val)
        except:
            return 0.0

# ==============================================================================
# 4. ONTOLOGY & FORENSIC ENGINE SERVICE
# ==============================================================================

class GBIOEngine:
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
        
        # Enforcement: CEX Deposit Rules
        if action == TransferAction.DEPOSITED_TO and target.entity_class not in [
            EntityClass.EXCHANGE_HOT, EntityClass.EXCHANGE_COLD, EntityClass.EXCHANGE_DEPOSIT, EntityClass.CUSTODIAN, EntityClass.OTC_BROKER
        ]:
            target.entity_class = EntityClass.EXCHANGE_DEPOSIT

        # Enforcement: Mixer Interaction Rules
        if action == TransferAction.MIXED_WITH and target.entity_class not in [
            EntityClass.MIXER_POOL, EntityClass.MIXER_ROUTER, EntityClass.COINJOIN_COORDINATOR, EntityClass.PRIVACY_POOL
        ]:
            target.entity_class = EntityClass.MIXER_ROUTER
            target.risk_profile.threat_level = ThreatLevel.CRITICAL
            if AMLFlag.MIXER_EXPOSURE not in target.risk_profile.aml_flags:
                target.risk_profile.aml_flags.append(AMLFlag.MIXER_EXPOSURE)

        # Enforcement: Bridge Routing Rules
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
        if not edges: return EntityClass.UNKNOWN
        relevant_edges = [e for e in edges if e.source_node_id == target_node_id or e.target_node_id == target_node_id]
        if not relevant_edges: return EntityClass.UNKNOWN

        in_edges = [e for e in relevant_edges if e.target_node_id == target_node_id]
        out_edges = [e for e in relevant_edges if e.source_node_id == target_node_id]
        
        in_degree = len(in_edges)
        out_degree = len(out_edges)
        unique_senders = len(set([e.source_node_id for e in in_edges]))
        unique_receivers = len(set([e.target_node_id for e in out_edges]))
        actions = [e.action for e in relevant_edges]
        action_counts = Counter(actions)

        if unique_senders > 500 and unique_receivers > 100:
            if action_counts.get(TransferAction.SWEPT_TO, 0) > 0 or action_counts.get(TransferAction.INTERNAL_TRANSFER, 0) > 50:
                return EntityClass.EXCHANGE_HOT
        if in_degree > 0 and out_degree > 0:
            if unique_receivers == 1 and unique_senders < 10:
                return EntityClass.EXCHANGE_DEPOSIT
        if action_counts.get(TransferAction.SWAPPED_TO, 0) > (len(relevant_edges) * 0.7):
            return EntityClass.DEX_ROUTER
        if action_counts.get(TransferAction.BRIDGED_TO, 0) > 0 or action_counts.get(TransferAction.BRIDGE_LOCKED, 0) > 0:
            return EntityClass.BRIDGE_ENDPOINT
        if action_counts.get(TransferAction.MINTED, 0) > 0 and unique_receivers > 500 and in_degree < 5:
            return EntityClass.MINING_POOL

        return EntityClass.EOA_WALLET

    @staticmethod
    def detect_behavioral_patterns(target_node_id: str, edges: List[GBIOEdge]) -> List[BehavioralIndicator]:
        indicators = set()
        out_edges = sorted([e for e in edges if e.source_node_id == target_node_id], key=lambda x: x.timestamp)
        in_edges = sorted([e for e in edges if e.target_node_id == target_node_id], key=lambda x: x.timestamp)
        
        unique_receivers = len(set([e.target_node_id for e in out_edges]))
        if len(out_edges) > 10 and unique_receivers > (len(out_edges) * 0.8):
            indicators.add(BehavioralIndicator.FAN_OUT)

        unique_senders = len(set([e.source_node_id for e in in_edges]))
        if len(in_edges) > 10 and unique_senders > (len(in_edges) * 0.8):
            indicators.add(BehavioralIndicator.FAN_IN)

        if in_edges and out_edges:
            for in_e in in_edges:
                for out_e in out_edges:
                    if out_e.timestamp >= in_e.timestamp:
                        time_diff = (out_e.timestamp - in_e.timestamp).total_seconds()
                        if 0 <= time_diff <= 30: 
                            indicators.add(BehavioralIndicator.RAPID_MOVEMENT)
                            break

        if len(in_edges) == 1 and len(out_edges) > 5:
            in_val = in_edges[0].amount_usd_estimate
            if in_val > 10000: 
                avg_out = sum(e.amount_usd_estimate for e in out_edges) / len(out_edges)
                if avg_out < (in_val * 0.2): 
                    indicators.add(BehavioralIndicator.PEELING_CHAIN)

        dex_actions = [e for e in out_edges if e.action == TransferAction.SWAPPED_TO]
        if len(dex_actions) >= 3:
            unique_assets = len(set([e.asset_symbol for e in dex_actions]))
            if unique_assets > 2:
                indicators.add(BehavioralIndicator.DEX_LAUNDERING)

        return list(indicators)

    @staticmethod
    def compute_aml_risk_profile(node: GBIONode, edges: List[GBIOEdge]) -> RiskProfile:
        profile = node.risk_profile
        base_score = 10.0 
        
        if profile.threat_level == ThreatLevel.SEVERE:
            profile.overall_score = 100.0
            if AMLFlag.OFAC_SANCTION_EXPOSURE not in profile.aml_flags:
                profile.aml_flags.append(AMLFlag.OFAC_SANCTION_EXPOSURE)
            return profile
        elif profile.threat_level == ThreatLevel.CRITICAL: base_score += 75.0
        elif profile.threat_level == ThreatLevel.HIGH: base_score += 50.0

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

class GBIONormalizer:
    """
    Production Normalizer mapping raw blockchain labels and entities to strict GBIO Ontology.
    Replaces the mock wrapper with deterministic string and semantic analysis.
    """
    @staticmethod
    def normalize_entity(target_entity: str, chain: str, raw_lbl: str, is_contract: bool):
        class NormalizedEntity:
            def __init__(self, e_class, label, threat):
                self.entity_class = e_class
                self.label = label
                self.threat_level = threat

        lbl_upper = (raw_lbl or "").upper()
        e_class = EntityClass.SMART_CONTRACT if is_contract else EntityClass.EOA_WALLET
        threat = ThreatLevel.LOW

        # 1. Threat Classification (Takes precedence)
        if any(k in lbl_upper for k in ["HACK", "EXPLOIT", "DRAIN", "PHISH", "SCAM"]):
            threat = ThreatLevel.CRITICAL
            e_class = EntityClass.EXPLOITER
        elif any(k in lbl_upper for k in ["SANCTION", "OFAC", "LAZARUS", "APT"]):
            threat = ThreatLevel.SEVERE
            e_class = EntityClass.SANCTIONED_ENTITY
        elif any(k in lbl_upper for k in ["MIXER", "TORNADO", "PRIVACY", "BLENDER"]):
            threat = ThreatLevel.HIGH
            e_class = EntityClass.MIXER_ROUTER

        # 2. Structural Classification
        if e_class in [EntityClass.SMART_CONTRACT, EntityClass.EOA_WALLET]:
            if any(k in lbl_upper for k in ["EXCHANGE", "BINANCE", "KRAKEN", "COINBASE", "CEX", "HUOBI", "OKX"]):
                e_class = EntityClass.EXCHANGE_DEPOSIT
                if "HOT" in lbl_upper: e_class = EntityClass.EXCHANGE_HOT
                elif "COLD" in lbl_upper: e_class = EntityClass.EXCHANGE_COLD
            elif any(k in lbl_upper for k in ["BRIDGE", "WORMHOLE", "LAYERZERO", "STARGATE", "ACROSS"]):
                e_class = EntityClass.BRIDGE_ENDPOINT
            elif any(k in lbl_upper for k in ["DEX", "SWAP", "ROUTER", "UNISWAP", "PANCAKE", "SUSHISWAP", "1INCH"]):
                e_class = EntityClass.DEX_ROUTER
            elif "OTC" in lbl_upper:
                e_class = EntityClass.OTC_BROKER
            elif any(k in lbl_upper for k in ["LENDING", "AAVE", "COMPOUND", "MAKER"]):
                e_class = EntityClass.LENDING_POOL

        return NormalizedEntity(e_class, raw_lbl, threat)