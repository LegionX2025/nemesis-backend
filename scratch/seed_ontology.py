from pymongo import MongoClient
import os

mongo_uri = os.getenv("DATABASE_MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client["nemesis"]
col = db["nemesis_ontology"]

# Clear existing ontology
col.delete_many({})

universal_matrix = {
    "type": "UNIVERSAL_MATRIX",
    "data": {
        "Bitcoin": {
            "Lock": "Script Hash (P2SH)",
            "Mint": "N/A",
            "Burn": "OP_RETURN",
            "Transfer": "UTXO SPEND",
            "Bridge": "WBTC Custody / Threshold Sig",
            "Exchange": "CEX Hot/Cold Deposit"
        },
        "Ethereum": {
            "Lock": "Smart Contract Vault",
            "Mint": "ERC20/ERC721 Mint",
            "Burn": "Address 0x0 / Burn Func",
            "Transfer": "ETH Native / ERC20 Transfer",
            "Bridge": "Cross-Chain Escrow",
            "Exchange": "CEX Omnibus Account"
        },
        "Tron": {
            "Lock": "TRC20 Lock",
            "Mint": "TRC20 Issue",
            "Burn": "TRC20 Burn",
            "Transfer": "TRX Native / TRC20 Transfer",
            "Bridge": "JustLend / BTTC Bridge",
            "Exchange": "CEX Deposit Address"
        },
        "Polygon": {
            "Lock": "PoS Bridge Lock",
            "Mint": "Wrapped Matic Mint",
            "Burn": "PoS Bridge Burn",
            "Transfer": "MATIC / ERC20",
            "Bridge": "PoS / Plasma Bridge",
            "Exchange": "CEX Multi-chain"
        },
        "BSC": {
            "Lock": "BEP20 Vault",
            "Mint": "BEP20 Mint",
            "Burn": "BEP20 Burn",
            "Transfer": "BNB / BEP20",
            "Bridge": "Binance Bridge",
            "Exchange": "Binance Hot Wallet"
        },
        "Solana": {
            "Lock": "Program PDA Lock",
            "Mint": "SPL Token Mint",
            "Burn": "SPL Burn",
            "Transfer": "SOL Native / SPL",
            "Bridge": "Wormhole Portal",
            "Exchange": "CEX Deposit"
        }
    }
}

scenarios = [
    {
        "scenario_id": "Tornado_Cash_Mixing",
        "chain": "Ethereum",
        "destination_chain": "Ethereum",
        "category": "Mixing / Obfuscation",
        "flow": "Suspect Wallet -> Tornado Cash Deposit -> Tornado Cash Relayer -> Clean Wallet",
        "state_transitions": ["NATIVE_DEPOSIT", "ZK_PROOF_GEN", "ANONYMOUS_WITHDRAWAL"],
        "fingerprints": ["TC_DEPOSIT_EVENT", "TC_WITHDRAWAL_EVENT", "EXACT_INCREMENTS"],
        "identity_signals": ["Timing Correlation", "Gas Price Heuristics", "Amount Matching"],
        "detection_logic": [
            {"stage": "Deposit", "detection": "Function: deposit() on known TC contract"},
            {"stage": "Withdrawal", "detection": "Function: withdraw() with zero-knowledge proof"},
            {"stage": "Correlation", "detection": "Heuristic matching of deposit and withdrawal within same block/timeframe"}
        ],
        "confidence_scoring": {
            "Deposit Event": 100,
            "Withdrawal Event": 100,
            "Link Correlation": 85
        }
    },
    {
        "scenario_id": "Cross_Chain_Bridge_Hop",
        "chain": "Bitcoin",
        "destination_chain": "Ethereum",
        "category": "Asset Re-denomination",
        "flow": "BTC Suspect -> Custodial Vault -> WBTC Mint -> Ethereum Suspect",
        "state_transitions": ["UTXO_LOCK", "CROSS_CHAIN_MSG", "ERC20_MINT"],
        "fingerprints": ["BTC_DEPOSIT", "MINT_EVENT", "BURN_EVENT"],
        "identity_signals": ["Merchant/Custody KYC", "Equivalent Value Output", "Timestamp Proximity"],
        "detection_logic": [
            {"stage": "Deposit", "detection": "BTC transfer to known custodian"},
            {"stage": "Mint", "detection": "WBTC Mint event on Ethereum"},
            {"stage": "Correlation", "detection": "Value match across chains with standard delay"}
        ],
        "confidence_scoring": {
            "BTC Deposit": 100,
            "WBTC Mint": 100,
            "Cross-chain Link": 92
        }
    }
]

col.insert_one(universal_matrix)
col.insert_many(scenarios)

print("Ontology seeded successfully.")
