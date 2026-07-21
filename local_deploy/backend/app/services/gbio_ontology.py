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

class OperationalStatus(str, Enum):
    ACTIVE = "Active"
    DORMANT = "Dormant"
    FROZEN = "Frozen"
    CLOSED = "Closed"
    ARCHIVED = "Archived"
    BURN_ADDRESS = "Burn Address"
    DESTROYED = "Destroyed"
    INACTIVE = "Inactive"
    MONITORING = "Monitoring"
    UNDER_INVESTIGATION = "Under Investigation"

class IntelligenceConfidence(str, Enum):
    VERIFIED = "Verified"
    HIGH_CONFIDENCE = "High Confidence"
    MEDIUM_CONFIDENCE = "Medium Confidence"
    LOW_CONFIDENCE = "Low Confidence"
    AI_INFERRED = "AI Inferred"
    HEURISTIC_MATCH = "Heuristic Match"
    MANUAL_ATTRIBUTION = "Manual Attribution"
    OSINT_VERIFIED = "OSINT Verified"

class WalletClassification(str, Enum):
    # Personal Wallets (EOA)
    PERSONAL_WALLET = "Personal Wallet"
    INDIVIDUAL_INVESTOR = "Individual Investor"
    RETAIL_USER = "Retail User"
    HNWI = "High-Net-Worth Individual (HNWI)"
    WHALE = "Whale"
    VIP_WALLET = "VIP Wallet"
    COLD_STORAGE = "Cold Storage"
    HOT_WALLET = "Hot Wallet"
    HARDWARE_WALLET = "Hardware Wallet"
    MOBILE_WALLET = "Mobile Wallet"
    BROWSER_WALLET = "Browser Wallet"
    MULTI_SIGNATURE_WALLET = "Multi-Signature Wallet"
    SMART_ACCOUNT = "Smart Account (ERC-4337)"

    # Centralized Exchange (CEX)
    EXCHANGE_DEPOSIT_WALLET = "Exchange Deposit Wallet"
    EXCHANGE_WITHDRAWAL_WALLET = "Exchange Withdrawal Wallet"
    EXCHANGE_HOT_WALLET = "Exchange Hot Wallet"
    EXCHANGE_COLD_WALLET = "Exchange Cold Wallet"
    EXCHANGE_TREASURY = "Exchange Treasury"
    EXCHANGE_OPERATIONS = "Exchange Operations"
    EXCHANGE_FEE_WALLET = "Exchange Fee Wallet"
    EXCHANGE_LIQUIDITY_WALLET = "Exchange Liquidity Wallet"
    EXCHANGE_CUSTODIAN = "Exchange Custodian"
    EXCHANGE_INTERNAL_WALLET = "Exchange Internal Wallet"

    # Custody Providers
    INSTITUTIONAL_CUSTODIAN = "Institutional Custodian"
    QUALIFIED_CUSTODIAN = "Qualified Custodian"
    MPC_WALLET = "MPC Wallet"
    ENTERPRISE_TREASURY = "Enterprise Treasury"
    ASSET_CUSTODIAN = "Asset Custodian"
    DIGITAL_BANK = "Digital Bank"
    TRUST_CUSTODIAN = "Trust Custodian"

    # OTC & Trading
    OTC_BROKER = "OTC Broker"
    OTC_DESK = "OTC Desk"
    MARKET_MAKER = "Market Maker"
    PROPRIETARY_TRADING = "Proprietary Trading"
    LIQUIDITY_PROVIDER = "Liquidity Provider"
    ARBITRAGE_WALLET = "Arbitrage Wallet"
    TREASURY_TRADING = "Treasury Trading"

    # DeFi
    LP_POSITION = "LP Position"
    STAKING_WALLET = "Staking Wallet"
    YIELD_FARMING = "Yield Farming"
    LENDING_PROTOCOL = "Lending Protocol"
    BORROWING_POSITION = "Borrowing Position"
    VAULT = "Vault"
    FARMING_CONTRACT = "Farming Contract"
    REWARDS_CONTRACT = "Rewards Contract"
    GOVERNANCE_WALLET = "Governance Wallet"

    # Smart Contracts
    SMART_CONTRACT = "Smart Contract"
    PROXY_CONTRACT = "Proxy Contract"
    UPGRADEABLE_CONTRACT = "Upgradeable Contract"
    FACTORY_CONTRACT = "Factory Contract"
    ROUTER_CONTRACT = "Router Contract"
    VAULT_CONTRACT = "Vault Contract"
    TREASURY_CONTRACT = "Treasury Contract"
    ORACLE_CONTRACT = "Oracle Contract"
    DAO_CONTRACT = "DAO Contract"
    TIMELOCK_CONTRACT = "Timelock Contract"

    # Bridges
    BRIDGE_CONTRACT = "Bridge Contract"
    BRIDGE_ESCROW = "Bridge Escrow"
    CROSS_CHAIN_VAULT = "Cross-Chain Vault"
    RELAY_WALLET = "Relay Wallet"
    VALIDATOR_WALLET = "Validator Wallet"
    BRIDGE_TREASURY = "Bridge Treasury"
    WRAPPED_ASSET_CUSTODIAN = "Wrapped Asset Custodian"

    # NFT
    NFT_HOLDER = "NFT Holder"
    NFT_MARKETPLACE = "NFT Marketplace"
    NFT_CREATOR = "NFT Creator"
    NFT_MINT_CONTRACT = "NFT Mint Contract"
    NFT_ROYALTY_WALLET = "NFT Royalty Wallet"
    NFT_TREASURY = "NFT Treasury"
    NFT_AUCTION_WALLET = "NFT Auction Wallet"

    # Stablecoin
    STABLECOIN_TREASURY = "Stablecoin Treasury"
    STABLECOIN_ISSUER = "Stablecoin Issuer"
    MINT_AUTHORITY = "Mint Authority"
    BURN_AUTHORITY = "Burn Authority"
    RESERVE_WALLET = "Reserve Wallet"

    # Token Issuers
    PROJECT_TREASURY = "Project Treasury"
    TOKEN_ISSUER = "Token Issuer"
    FOUNDATION_WALLET = "Foundation Wallet"
    ECOSYSTEM_FUND = "Ecosystem Fund"
    TEAM_ALLOCATION = "Team Allocation"
    VESTING_WALLET = "Vesting Wallet"
    INVESTOR_ALLOCATION = "Investor Allocation"
    MARKETING_WALLET = "Marketing Wallet"

    # Validators & Mining
    VALIDATOR = "Validator"
    STAKING_VALIDATOR = "Staking Validator"
    CONSENSUS_NODE = "Consensus Node"
    MINING_POOL = "Mining Pool"
    VALIDATOR_TREASURY = "Validator Treasury"
    DELEGATOR = "Delegator"
    MINER = "Miner"
    MINING_REWARD = "Mining Reward"
    COINBASE_REWARD_WALLET = "Coinbase Reward Wallet"

    # DAO & Infrastructure
    DAO_TREASURY = "DAO Treasury"
    DAO_MULTISIG = "DAO Multisig"
    COMMUNITY_TREASURY = "Community Treasury"
    PROPOSAL_EXECUTOR = "Proposal Executor"
    ORACLE = "Oracle"
    KEEPER = "Keeper"
    RELAYER = "Relayer"
    SEQUENCER = "Sequencer"
    RPC_INFRASTRUCTURE = "RPC Infrastructure"
    CROSS_CHAIN_RELAYER = "Cross-Chain Relayer"

    # Payment & Enterprise
    MERCHANT = "Merchant"
    PAYMENT_GATEWAY = "Payment Gateway"
    PAYROLL_WALLET = "Payroll Wallet"
    SALARY_WALLET = "Salary Wallet"
    INVOICE_WALLET = "Invoice Wallet"
    ESCROW = "Escrow"
    SUBSCRIPTION_WALLET = "Subscription Wallet"
    CORPORATE_TREASURY = "Corporate Treasury"
    BUSINESS_WALLET = "Business Wallet"
    VENDOR_WALLET = "Vendor Wallet"
    SUPPLIER_WALLET = "Supplier Wallet"
    PAYROLL_TREASURY = "Payroll Treasury"
    OPERATIONAL_WALLET = "Operational Wallet"

    # Government / Public Sector / Non-Profit
    GOVERNMENT_TREASURY = "Government Treasury"
    TAX_COLLECTION = "Tax Collection"
    PUBLIC_AGENCY = "Public Agency"
    CBDC_AUTHORITY = "CBDC Authority"
    LAW_ENFORCEMENT_SEIZURE_WALLET = "Law Enforcement Seizure Wallet"
    COURT_CUSTODY_WALLET = "Court Custody Wallet"
    CHARITY = "Charity"
    DONATION_WALLET = "Donation Wallet"
    RELIEF_FUND = "Relief Fund"
    FOUNDATION = "Foundation"

    # High-Risk Categories
    MIXER_DEPOSIT = "Mixer Deposit"
    MIXER_WITHDRAWAL = "Mixer Withdrawal"
    MIXER_TREASURY = "Mixer Treasury"
    MIXING_POOL = "Mixing Pool"
    COINJOIN_PARTICIPANT = "CoinJoin Participant"
    PRIVACY_POOL = "Privacy Pool"
    PRIVACY_WALLET = "Privacy Wallet"
    SHIELDED_ADDRESS = "Shielded Address"
    ANONYMOUS_SERVICE = "Anonymous Service"
    OBFUSCATION_WALLET = "Obfuscation Wallet"
    DARKNET_MARKET = "Darknet Market"
    DARKNET_VENDOR_WALLET = "Vendor Wallet"
    MARKETPLACE_TREASURY = "Marketplace Treasury"
    ESCROW_WALLET = "Escrow Wallet"

    # Fraud & Malware
    SCAM_WALLET = "Scam Wallet"
    INVESTMENT_SCAM = "Investment Scam"
    RUG_PULL = "Rug Pull"
    PONZI = "Ponzi"
    FAKE_AIRDROP = "Fake Airdrop"
    FAKE_GIVEAWAY = "Fake Giveaway"
    FAKE_TOKEN = "Fake Token"
    PHISHING_WALLET = "Phishing Wallet"
    ROMANCE_SCAM = "Romance Scam"
    IMPERSONATION = "Impersonation"
    MALWARE_WALLET = "Malware Wallet"
    BOTNET_CONTROLLER = "Botnet Controller"
    INFOSTEALER = "Infostealer"
    CLIPBOARD_HIJACKER = "Clipboard Hijacker"
    CRYPTOJACKER = "Cryptojacker"

    # Ransomware & Sanctions
    RANSOMWARE = "Ransomware"
    INITIAL_PAYMENT_WALLET = "Initial Payment Wallet"
    AFFILIATE_WALLET = "Affiliate Wallet"
    CASH_OUT_WALLET = "Cash-out Wallet"
    OFAC_LISTED = "OFAC Listed"
    SANCTIONED_ENTITY = "Sanctioned Entity"
    TERROR_FINANCING = "Terror Financing"
    EXTREMIST_FINANCING = "Extremist Financing"
    STATE_SPONSORED = "State-Sponsored"
    PROLIFERATION_FINANCING = "Proliferation Financing"

    # Hacking & Investigation
    EXPLOIT_WALLET = "Exploit Wallet"
    HACKER_WALLET = "Hacker Wallet"
    DRAINER = "Drainer"
    FLASH_LOAN_EXPLOIT = "Flash Loan Exploit"
    SMART_CONTRACT_EXPLOIT = "Smart Contract Exploit"
    BRIDGE_EXPLOIT = "Bridge Exploit"
    MEV_BOT = "MEV Bot"
    SANDWICH_BOT = "Sandwich Bot"
    ARBITRAGE_BOT = "Arbitrage Bot"
    PERSON_OF_INTEREST = "Person of Interest"
    PRIMARY_SUBJECT = "Primary Subject"
    SECONDARY_SUBJECT = "Secondary Subject"
    WITNESS_WALLET = "Witness Wallet"
    VICTIM_WALLET = "Victim Wallet"
    EVIDENCE_WALLET = "Evidence Wallet"
    SEIZED_WALLET = "Seized Wallet"
    UNDER_SURVEILLANCE = "Under Surveillance"
    WATCHLIST = "Watchlist"
    LINKED_ENTITY = "Linked Entity"
    CLUSTER_MEMBER = "Cluster Member"
    UNKNOWN = "Unknown"

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
    
    risk_profile: RiskProfile = Field(default_factory=RiskProfile)
    
    # Advanced Identity & Taxonomy (NEMESIS ID Standard)
    primary_classification: WalletClassification = Field(default=WalletClassification.UNKNOWN)
    secondary_classifications: List[WalletClassification] = Field(default_factory=list)
    intelligence_confidence: IntelligenceConfidence = Field(default=IntelligenceConfidence.AI_INFERRED)
    operational_status: OperationalStatus = Field(default=OperationalStatus.ACTIVE)
    entity_type: str = Field(default="Unknown", description="e.g. Organization, Individual, Automated Bot")
    
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

class GBIONormalizer:
    @staticmethod
    def normalize_entity(target_entity, chain, raw_lbl, is_contract):
        class NormalizedEntity:
            def __init__(self, e, l, c):
                self.entity_class = EntityClass.EXCHANGE_DEPOSIT if "EXCHANGE" in l else EntityClass.EOA_WALLET
                self.label = l
                self.threat_level = ThreatLevel.LOW
        return NormalizedEntity(target_entity, raw_lbl, is_contract)
