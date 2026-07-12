# services/ontology.py

"""
Comprehensive Blockchain Taxonomy
Suitable for blockchain intelligence, digital forensics, AML, compliance, threat intelligence, and graph analytics systems.
Canonical ontology across all major networks.
"""

LAYER_0 = [
    "Polkadot", "Kusama", "Cosmos", "Cosmos Hub", "Celestia", "EigenLayer", 
    "Avalanche Subnets", "Axelar", "Wormhole", "Hyperlane", "LayerZero", 
    "Chainlink CCIP", "Quant Overledger", "zkBridge", "Router Protocol"
]

LAYER_1 = {
    "Bitcoin Family": [
        "Bitcoin", "Litecoin", "Dogecoin", "Bitcoin Cash", "Bitcoin SV", 
        "Dash", "DigiByte", "Zcash", "Monero", "Verge", "Ravencoin", "eCash", "Decred"
    ],
    "Ethereum Ecosystem": ["Ethereum Mainnet", "Ethereum Classic"],
    "Smart Contract Layer-1": [
        "BNB Smart Chain", "Solana", "Avalanche C-Chain", "Tron", "Cardano", 
        "Near", "Algorand", "Hedera", "Aptos", "Sui", "Sei", "Fantom", "Cronos", 
        "Kava", "Celo", "Harmony", "Moonbeam", "Moonriver", "Aurora", "Evmos", 
        "Telos", "EOS", "WAX", "VeChain", "Internet Computer", "Tezos", "Flow", 
        "Klaytn", "Kaia", "TON", "XRP Ledger", "Stellar", "Casper", "Oasis", 
        "Mina", "Aleph Zero", "Concordium"
    ]
}

LAYER_2 = {
    "Optimistic Rollups": ["Optimism", "Base", "Mantle", "Boba", "Blast", "Mode"],
    "ZK Rollups": ["zkSync Era", "Starknet", "Linea", "Scroll", "Polygon zkEVM", "Taiko"],
    "Sidechains": ["Polygon PoS", "Gnosis", "Ronin", "Palm", "SKALE", "Rootstock"]
}

APP_CHAINS = [
    "dYdX Chain", "Osmosis", "Injective", "Kujira", "Juno", "Secret", 
    "Terra", "Terra Classic", "Berachain", "Monad", "Sonic"
]

ENTERPRISE_CHAINS = [
    "Hyperledger Fabric", "Hyperledger Besu", "Hyperledger Sawtooth", 
    "Quorum", "Corda", "Multichain", "AntChain"
]

PRIVACY_CHAINS = ["Monero", "Zcash", "Secret Network", "Aleo", "IronFish"]
ROLLUP_TYPES = ["Validium", "Plasma", "zkRollup", "Optimistic Rollup"]
MODULAR_CHAINS = ["Celestia", "Avail", "EigenDA", "Fuel"]
PAYMENT_NETWORKS = ["Ripple", "Stellar", "Lightning Network", "Liquid Network"]
NFT_NETWORKS = ["Immutable X", "Ronin", "Flow", "Palm"]
DEPIN = ["Helium", "IoTeX", "Peaq"]
AI_CHAINS = ["Bittensor", "Fetch.ai", "Oraichain"]

CROSS_CHAIN_PROTOCOLS = {
    "Native Bridges": [
        "Arbitrum Bridge", "Optimism Bridge", "Base Bridge", "Polygon Bridge", 
        "Avalanche Bridge", "Solana Wormhole", "BNB Bridge"
    ],
    "Third-party Bridges": [
        "Wormhole", "LayerZero", "Axelar", "Hyperlane", "Stargate", "Synapse", 
        "Celer cBridge", "Multichain", "Across", "deBridge", "Router Protocol", 
        "ChainPort", "Orbiter", "Hop", "Portal", "Ren Bridge", "THORChain"
    ]
}

WALLET_TYPES = {
    "Externally Owned": ["Single Signature", "Multi Signature", "MPC Wallet", "Smart Wallet"],
    "Custodial": ["Exchange", "Institution", "Custodian", "Broker"],
    "Smart Contract Wallet": ["Safe", "Argent", "Coinbase Smart Wallet", "ERC-4337"]
}

TRANSACTION_CATEGORIES = {
    "Native Transfer": ["ETH Transfer", "BTC Transfer", "SOL Transfer", "TRX Transfer", "XRP Payment", "ADA Transfer"],
    "Token Transfer": ["ERC20", "ERC721", "ERC1155", "SPL", "TRC10", "TRC20", "BEP20", "BEP721", "CW20", "Jetton", "ARC200"],
    "Internal Transfer": ["Internal ETH", "Internal Contract Call", "Delegate Call", "Static Call", "Call Code"],
    "Smart Contract": ["Contract Deployment", "Contract Interaction", "Proxy Upgrade", "Factory Deployment", "CREATE", "CREATE2", "Selfdestruct"],
    "Governance": ["Vote", "Proposal", "Delegate", "Undelegate", "Validator Vote"],
    "Staking": ["Stake", "Unstake", "Restake", "Delegate", "Redelegate", "Claim Rewards", "Compound Rewards", "Validator Bond", "Validator Unbond"],
    "Validator": ["Block Production", "Attestation", "Slashing", "Validator Registration", "Validator Exit"],
    "DeFi": ["Swap", "Multi-hop Swap", "Liquidity Add", "Liquidity Remove", "Flash Loan", "Borrow", "Repay", "Deposit", "Withdraw", "Leverage", "Yield Farm", "Harvest", "Auto Compound", "Mint LP", "Burn LP", "Vault Deposit", "Vault Withdraw", "Stable Swap", "Liquidation", "Margin Open", "Margin Close"],
    "NFT": ["Mint", "Burn", "Transfer", "Safe Transfer", "Auction", "Bid", "Buy", "Sell", "Listing", "Delisting", "Royalty Payment", "Fractionalization"],
    "Marketplace": ["Purchase", "Sale", "Offer", "Cancel Offer", "Escrow", "Settlement"],
    "Cross-chain": ["Bridge Deposit", "Bridge Withdrawal", "Bridge Lock", "Bridge Unlock", "Bridge Mint", "Bridge Burn", "Message Relay", "Cross-chain Swap", "Cross-chain Call", "Cross-chain Execution", "Cross-chain Liquidity"],
    "Lightning": ["Channel Open", "Channel Close", "Force Close", "HTLC", "Routing Payment", "Rebalance"],
    "Privacy": ["Shield", "Unshield", "Mixer Deposit", "Mixer Withdrawal", "Ring Signature Spend", "zk Proof Transfer"],
    "Mining": ["Coinbase Reward", "Mining Reward", "Uncle Reward", "Fee Reward"],
    "MEV": ["Sandwich Attack", "Arbitrage", "Backrun", "Frontrun", "Bundle", "Liquidation Bot", "JIT Liquidity"],
    "Security": ["Rug Pull", "Honeypot", "Exploit", "Flash Loan Attack", "Oracle Manipulation", "Governance Attack", "Bridge Exploit", "Replay Attack", "Sybil Attack", "Dusting Attack"]
}

TRANSACTION_EVENTS = {
    "Token Events": ["Transfer", "Approval", "Mint", "Burn", "Freeze", "Unfreeze", "Blacklist", "Whitelist"],
    "ERC-20": ["Transfer", "Approval"],
    "ERC-721": ["Transfer", "Approval", "ApprovalForAll"],
    "ERC-1155": ["TransferSingle", "TransferBatch", "URI", "ApprovalForAll"],
    "DeFi Events": ["Swap", "Sync", "Mint", "Burn", "Deposit", "Withdraw", "Borrow", "Repay", "Liquidate", "FlashLoan", "Harvest"],
    "Staking Events": ["Stake", "Unstake", "Delegate", "Undelegate", "RewardPaid", "Restake"],
    "Governance Events": ["ProposalCreated", "VoteCast", "ProposalExecuted", "ProposalCanceled", "DelegateChanged"],
    "Bridge Events": ["Locked", "Released", "Minted", "Burned", "MessageSent", "MessageReceived", "ProofVerified"],
    "Smart Contract Events": ["OwnershipTransferred", "Upgraded", "Initialized", "Paused", "Unpaused", "RoleGranted", "RoleRevoked", "ProxyCreated"],
    "Wallet Events": ["WalletCreated", "WalletRecovered", "SignerAdded", "SignerRemoved", "ThresholdChanged"],
    "Validator Events": ["ValidatorJoined", "ValidatorLeft", "Slashed", "Jailed", "Unjailed"]
}

TRANSACTION_STATUS = [
    "Pending", "Queued", "Submitted", "Broadcast", "Included", "Confirmed", 
    "Finalized", "Safe", "Executed", "Failed", "Reverted", "Dropped", 
    "Expired", "Replaced", "Cancelled", "Orphaned", "Reorged"
]

FLOW_TYPES = [
    "Wallet → Wallet", "Wallet → Exchange", "Exchange → Wallet", "Exchange → Exchange", 
    "Wallet → Bridge", "Bridge → Wallet", "Wallet → Mixer", "Mixer → Wallet", 
    "Wallet → DeFi", "DeFi → Wallet", "Wallet → NFT Marketplace", "NFT Marketplace → Wallet", 
    "Wallet → Smart Contract", "Smart Contract → Wallet", "Contract → Contract", 
    "Wallet → Validator", "Validator → Wallet", "Wallet → Treasury", "Treasury → Wallet", 
    "Wallet → DAO", "DAO → Wallet", "Wallet → Custodian", "Custodian → Wallet", 
    "Wallet → OTC Desk", "OTC Desk → Wallet", "Wallet → Payment Processor", 
    "Payment Processor → Merchant", "Merchant → Wallet", "Wallet → Cross-chain Bridge", 
    "Cross-chain Bridge → Destination Wallet", "Wallet → Layer 2", "Layer 2 → Layer 1", 
    "Wallet → Rollup", "Rollup → Wallet"
]

ENTITY_TYPES = [
    "Individual Wallet", "Smart Contract", "Exchange", "DEX", "CEX", "Bridge", 
    "Validator", "Miner", "DAO", "Treasury", "DeFi Protocol", "Lending Protocol", 
    "NFT Marketplace", "NFT Collection", "Stablecoin Issuer", "Custodian", 
    "OTC Desk", "Payment Processor", "Merchant", "Institutional Wallet", 
    "Government Wallet", "Sanctioned Entity", "Mixer / Privacy Protocol", 
    "MEV Searcher", "Builder", "Relayer", "Sequencer", "Oracle", 
    "Cross-chain Router", "Multisig Wallet", "MPC Wallet", "Factory Contract", 
    "Proxy Contract", "Token Contract", "Wrapped Asset Contract", 
    "Escrow Contract", "Vesting Contract", "Bridge Contract"
]

def map_tx_to_ontology(tx_info: dict) -> dict:
    """
    Helper function to classify an unknown transaction into the taxonomy.
    Takes a dict containing 'from_entity', 'to_entity', 'method_name', 'edge_type', etc.
    Returns classified dict with 'flow_type', 'tx_category', 'event_type'.
    """
    edge_type = tx_info.get("edge_type", "").upper()
    intent_action = tx_info.get("intent_action", "").upper()
    
    flow_type = "Wallet → Wallet"
    tx_category = "Native Transfer"
    
    if "MIXER" in edge_type or "TORNADO" in intent_action:
        flow_type = "Wallet → Mixer"
        tx_category = "Privacy"
    elif "BRIDGE" in edge_type:
        flow_type = "Wallet → Cross-chain Bridge"
        tx_category = "Cross-chain"
    elif "SWAP" in edge_type or "DEX" in intent_action:
        flow_type = "Wallet → DeFi"
        tx_category = "DeFi"
    elif "EXCHANGE" in tx_info.get("receiver_entity", "").upper():
        flow_type = "Wallet → Exchange"
        tx_category = "Native Transfer"
    
    return {
        "flow_type": flow_type,
        "tx_category": tx_category,
        "event_type": tx_info.get("action", "Transfer")
    }

# --- NEW FROM GBEO v3 SPEC ---

WALLET_CLASSIFICATION_ONTOLOGY = [
    "Private Wallet", "Personal Wallet", "Exchange", "Exchange Deposit", 
    "Exchange Hot Wallet", "Exchange Cold Wallet", "Custodial Wallet", 
    "Treasury", "Smart Contract", "Proxy Contract", "Upgradeable Contract", 
    "Bridge", "Bridge Relayer", "DEX", "Liquidity Pool", "Router", 
    "Factory", "Vault", "Token Contract", "NFT Collection", "Validator", 
    "Mining Pool", "Staking Pool", "DAO Treasury", "Foundation", 
    "Market Maker", "OTC Broker", "Payment Processor", "Custodian", 
    "Whale", "Government", "Law Enforcement", "Mixer", "Privacy Protocol", 
    "Flash Loan Contract", "MEV Bot", "Arbitrage Bot", "Liquidation Bot", 
    "Cross-Chain Router", "Scam", "Phishing", "Wallet Drainer", 
    "Exploiter", "Sanctioned", "Darknet Market", "Ransomware", "Fraud", "Unknown"
]

IDENTITY_FINGERPRINT = {
    "Wallet Type": [],
    "Account Model": ["UTXO", "Account"],
    "Address Format": [],
    "Checksum": [],
    "Script Type": [],
    "Curve": ["secp256k1", "ed25519"],
    "Signature Type": [],
    "Multisig": [],
    "Safe": [],
    "Contract": [],
    "Proxy": [],
    "Factory": [],
    "Implementation": []
}

BEHAVIORAL_FINGERPRINT = [
    "Transaction frequency", "Transaction interval", "Time of day", 
    "Weekday activity", "Weekend activity", "Gas preference", 
    "Priority fee behavior", "Nonce pattern", "Dust generation", 
    "Average transaction size", "Largest transaction", "Average holding period", 
    "Transfer cadence", "Wallet lifetime", "First activity", 
    "Recent activity", "Dormancy", "Reactivation"
]

FINANCIAL_FINGERPRINT = [
    "Portfolio value", "Token diversity", "Stablecoin ratio", 
    "NFT ratio", "Native token ratio", "LP exposure", "Yield farming", 
    "DEX usage", "Bridge usage", "CEX usage", "Mixer exposure", 
    "OTC exposure", "Treasury exposure"
]

OBFUSCATION_DETECTION = {
    "Layering": [
        "Rapid forwarding", "Chain hopping", "Repeated intermediate wallets", 
        "Micro-transfers", "Large split transfers", "Consolidation", 
        "Peel chains", "Circular movement", "Fan-out", "Fan-in"
    ],
    "Mixer Detection": [
        "Tornado Cash", "CoinJoin", "Whirlpool", "Railgun", "Privacy pools"
    ]
}

INDICATORS_LIBRARY = {
    "AML Indicators": [
        "Sanction Exposure", "High Risk Jurisdiction", "Exchange Exposure", 
        "Mixer Exposure", "Darknet Exposure", "Ransomware Exposure", 
        "Scam Exposure", "Exploit Exposure", "Fraud Exposure", "Bridge Abuse"
    ],
    "Behavioral Indicators": [
        "High Velocity", "Dormant Reactivation", "Flash Wallet", 
        "One-Time Wallet", "Treasury Wallet", "Liquidity Provider", 
        "MEV", "Arbitrage", "Validator", "Mining Pool", "Whale", 
        "Dusting", "Bridge Hopper"
    ],
    "Infrastructure Indicators": [
        "Proxy", "Upgradeable", "Factory", "Clone", "Safe", "Multisig", 
        "CREATE2", "AA Wallet", "ERC4337", "Bundler"
    ]
}
