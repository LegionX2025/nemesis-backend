"""
Global Blockchain Explorer Ontology (GBEO) v3
Defines the canonical URLs and taxonomy for 5 Major Explorer Families.
"""

UNIVERSAL_VARIABLES = {
    "address": "Wallet / Account / Smart Contract",
    "txhash": "Transaction Hash / Signature",
    "token": "Token Contract / Mint",
    "tokenId": "NFT Token ID",
    "collection": "NFT Collection",
    "block": "Block Height",
    "validator": "Validator Address",
    "ens": "ENS / Domain",
    "program": "Solana Program",
    "bridge": "Bridge Contract",
    "pool": "Liquidity Pool",
    "pair": "Trading Pair",
    "epoch": "Validator Epoch",
    "slot": "Solana Slot"
}

ENTITY_TYPES = [
    "Wallet", "Person", "Organization", "Exchange", "Custodian", "Bridge",
    "Mixer", "Validator", "DAO", "Smart Contract", "NFT Collection",
    "Token", "Stablecoin", "DeFi Protocol", "Sanction List Entry"
]

EDGE_TYPES = [
    "SENT_TO", "RECEIVED_FROM", "MINTED", "BURNED", "WRAPPED_AS", "UNWRAPPED_TO",
    "LOCKED", "UNLOCKED", "BRIDGED_TO", "BRIDGED_FROM", "MESSAGE_SENT",
    "MESSAGE_RECEIVED", "SWAPPED_TO", "ADDED_LIQUIDITY", "REMOVED_LIQUIDITY",
    "STAKED", "UNSTAKED", "BORROWED", "REPAID", "FLASH_LOAN", "LIQUIDATED",
    "APPROVED", "TRANSFERRED_NFT", "DEPLOYED_CONTRACT", "EXECUTED",
    "INTERACTED_WITH", "DEPOSITED_TO", "WITHDREW_FROM", "CONSOLIDATED",
    "HOT_WALLET", "COLD_WALLET", "MIXED", "COINJOIN", "TORNADO",
    "SANCTIONED", "HIGH_RISK"
]

WALLET_CLASSIFICATION_ONTOLOGY = [
    "Private Wallet", "Personal Wallet", "Exchange", "Exchange Deposit", 
    "Exchange Hot Wallet", "Exchange Cold Wallet", "Custodial Wallet", 
    "Treasury", "Smart Contract", "Proxy Contract", "Upgradeable Contract", 
    "Bridge", "Bridge Relayer", "DEX", "Liquidity Pool", "Router", "Factory", 
    "Vault", "Token Contract", "NFT Collection", "Validator", "Mining Pool", 
    "Staking Pool", "DAO Treasury", "Foundation", "Market Maker", "OTC Broker", 
    "Payment Processor", "Custodian", "Whale", "Government", "Law Enforcement", 
    "Mixer", "Privacy Protocol", "Flash Loan Contract", "MEV Bot", "Arbitrage Bot", 
    "Liquidation Bot", "Cross-Chain Router", "Scam", "Phishing", "Wallet Drainer", 
    "Exploiter", "Sanctioned", "Darknet Market", "Ransomware", "Fraud", "Unknown",
    "Burn Address", "Null Address"
]

EXPLORER_FAMILIES = {
    "EVM": {
        "ETH": {"base": "https://etherscan.io", "type": "etherscan"},
        "BSC": {"base": "https://bscscan.com", "type": "etherscan"},
        "POLYGON": {"base": "https://polygonscan.com", "type": "etherscan"},
        "BASE": {"base": "https://basescan.org", "type": "etherscan"},
        "ARBITRUM": {"base": "https://arbiscan.io", "type": "etherscan"},
        "OPTIMISM": {"base": "https://optimistic.etherscan.io", "type": "etherscan"},
        "AVALANCHE": {"base": "https://snowtrace.io", "type": "etherscan"},
        "FANTOM": {"base": "https://ftmscan.com", "type": "etherscan"},
        "LINEA": {"base": "https://lineascan.build", "type": "etherscan"},
        "CELO": {"base": "https://celoscan.io", "type": "etherscan"},
        "ZKSYNC": {"base": "https://explorer.zksync.io", "type": "blockscout"}, # some are blockscout
        "MANTLE": {"base": "https://explorer.mantle.xyz", "type": "blockscout"},
        "GNOSIS": {"base": "https://gnosisscan.io", "type": "etherscan"}
    },
    "UTXO": {
        "BTC": {"base": "https://mempool.space", "type": "mempool"},
        "LTC": {"base": "https://blockchair.com/litecoin", "type": "blockchair"},
        "DOGE": {"base": "https://blockchair.com/dogecoin", "type": "blockchair"}
    },
    "NON_EVM": {
        "SOL": {"base": "https://solscan.io", "type": "solscan"},
        "TRX": {"base": "https://tronscan.org/#", "type": "tronscan"},
        "XRP": {"base": "https://xrpscan.com", "type": "xrpscan"},
        "TON": {"base": "https://tonviewer.com", "type": "tonviewer"},
        "NEAR": {"base": "https://nearblocks.io", "type": "nearblocks"},
        "APTOS": {"base": "https://explorer.aptoslabs.com", "type": "aptos"},
        "SUI": {"base": "https://suivision.xyz", "type": "sui"},
        "COSMOS": {"base": "https://www.mintscan.io/cosmos", "type": "mintscan"}
    },
    "INTELLIGENCE": {
        "OKLINK": {"base": "https://www.oklink.com", "type": "oklink"}
    }
}

def get_canonical_endpoints(explorer_type: str, base_url: str) -> dict:
    if explorer_type == "etherscan":
        return {
            "wallet": f"{base_url}/address/{{address}}",
            "tx": f"{base_url}/tx/{{txhash}}",
            "token": f"{base_url}/token/{{token}}",
            "analytics": f"{base_url}/address/{{address}}#analytics"
        }
    elif explorer_type == "blockscout":
        return {
            "wallet": f"{base_url}/address/{{address}}",
            "tx": f"{base_url}/tx/{{txhash}}",
            "token": f"{base_url}/token/{{token}}",
            "analytics": f"{base_url}/address/{{address}}?tab=analytics"
        }
    elif explorer_type == "mempool":
        return {
            "wallet": f"{base_url}/address/{{address}}",
            "tx": f"{base_url}/tx/{{txhash}}"
        }
    elif explorer_type == "solscan":
        return {
            "wallet": f"{base_url}/account/{{address}}",
            "tx": f"{base_url}/tx/{{txhash}}",
            "token": f"{base_url}/token/{{token}}"
        }
    elif explorer_type == "oklink":
        return {
            "wallet": f"{base_url}/{{chain_lower}}/address/{{address}}",
            "tx": f"{base_url}/{{chain_lower}}/tx/{{txhash}}"
        }
    else:
        return {
            "wallet": f"{base_url}/address/{{address}}",
            "tx": f"{base_url}/tx/{{txhash}}"
        }
