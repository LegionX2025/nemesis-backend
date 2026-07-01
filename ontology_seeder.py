import os
import sys
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OntologySeeder")

load_dotenv()

MONGO_URI = "mongodb+srv://MKpBkrUw:Z63zGHQaiYG6rhrb@us-east-1.ufsuw.mongodb.net/blockchain"
DB_NAME = "nemesis"
COLLECTION_NAME = "nemesis_ontology"

ONTOLOGY_DATA = [
    {
        "scenario_id": "BTC_WBTC_CROSS_CHAIN",
        "chain": "Bitcoin",
        "destination_chain": "Ethereum",
        "category": "Wrapping / Cross-Chain Hop",
        "flow": "BTC -> BitGo Custody -> WBTC Mint -> Ethereum -> Uniswap -> Arbitrum -> Binance",
        "state_transitions": [
            "UTXO Created", "BTC Locked", "Custodian Confirmation", "ERC20 Mint", 
            "Transfer", "DEX Swap", "Bridge Lock", "Bridge Mint", "Swap", "Exchange Deposit"
        ],
        "detection_logic": [
            {"stage": "BTC", "detection": "Large UTXO entering BitGo custody"},
            {"stage": "WBTC", "detection": "Mint event from WBTC contract"},
            {"stage": "Ethereum", "detection": "ERC20 Transfer events"},
            {"stage": "Uniswap", "detection": "Swap() emitted"},
            {"stage": "Bridge", "detection": "Deposit() Lock() MessageSent()"},
            {"stage": "Arbitrum", "detection": "Mint event"},
            {"stage": "Binance", "detection": "Known exchange deposit cluster"}
        ],
        "fingerprints": [
            "BitGo custody", "WBTC contract", "Mint()", "ERC20 Transfer", "Uniswap Router", "Arbitrum Gateway", "Binance deposit address"
        ],
        "identity_signals": ["Same transaction timing", "Same USD value", "Bridge nonce", "Mint amount", "Deposit amount", "Exchange cluster"],
        "confidence_scoring": {
            "Bridge Event": 100, "Mint Event": 100, "Exchange Cluster": 99, "Value Match": 98, "Timing Match": 97, "Gas Pattern": 94, "Identity Cluster": 93
        }
    },
    {
        "scenario_id": "BTC_COINJOIN_TRON",
        "chain": "Bitcoin",
        "destination_chain": "TRON",
        "category": "Mixing & OTC Bridging",
        "flow": "BTC -> CoinJoin -> OTC -> USDT(TRON) -> JustLend",
        "state_transitions": [
            "UTXO", "CoinJoin", "Exit UTXO", "Exchange", "USDT", "TRON", "JustLend"
        ],
        "detection_logic": [
            {"stage": "CoinJoin", "detection": "Equal Outputs, Common Input Ownership Broken"},
            {"stage": "OTC Wallet", "detection": "Large TRON Deposit"},
            {"stage": "TRON", "detection": "TRC20 Transfer"},
            {"stage": "JustLend", "detection": "JustLend Deposit"}
        ],
        "fingerprints": [
            "Equal outputs", "Multi-input transaction", "Whirlpool / Wasabi pattern", "OTC wallet cluster", "Known TRON exchange", "JustLend contract interaction"
        ],
        "identity_signals": ["Equal denomination outputs", "Input/Output count", "Change heuristic", "TRC20 Transfer", "Internal transaction"],
        "confidence_scoring": {
            "CoinJoin Pattern": 98, "TRON Exchange Cluster": 95, "OTC Correlation": 85
        }
    },
    {
        "scenario_id": "ETH_LIDO_AAVE",
        "chain": "Ethereum",
        "destination_chain": "Ethereum",
        "category": "DeFi / Liquid Staking",
        "flow": "ETH -> Lido -> stETH -> Aave",
        "state_transitions": [
            "Deposit()", "stETH Mint", "ERC20 Transfer", "Approval", "Deposit()"
        ],
        "detection_logic": [
            {"stage": "Deposit()", "detection": "ETH enters Lido"},
            {"stage": "stETH Mint", "detection": "Liquid staking"},
            {"stage": "ERC20 Transfer", "detection": "Wallet receives stETH"},
            {"stage": "Approval", "detection": "Aave"},
            {"stage": "Deposit()", "detection": "Collateral supplied"}
        ],
        "fingerprints": ["Lido Contract", "stETH Mint", "Approval", "Aave Lending Pool"],
        "identity_signals": ["Same wallet", "Smart Contract Sequences"],
        "confidence_scoring": {"Lido Contract Match": 100, "Aave Deposit": 100}
    },
    {
        "scenario_id": "XRP_STELLAR_ETH",
        "chain": "XRP",
        "destination_chain": "Ethereum",
        "category": "Inter-Ledger Bridging",
        "flow": "XRP -> Anchor -> Stellar -> Ethereum",
        "state_transitions": ["XRP Memo", "Anchor", "Issued Asset", "Bridge", "ERC20 Mint"],
        "detection_logic": [
            {"stage": "XRP Memo", "detection": "Destination Tag / Memo parsing"},
            {"stage": "Stellar", "detection": "Issued Asset -> Bridge"},
            {"stage": "Ethereum", "detection": "ERC20 Mint"}
        ],
        "fingerprints": ["XRP Memo", "Destination Tag", "Stellar Anchor", "Federation", "Ethereum Mint"],
        "identity_signals": ["Memo correlation", "Value Match", "Timestamp Match"],
        "confidence_scoring": {"Memo Match": 100, "Ethereum Mint": 95}
    },
    {
        "scenario_id": "SOL_WORMHOLE_ETH",
        "chain": "Solana",
        "destination_chain": "Ethereum",
        "category": "Message Passing / Bridging",
        "flow": "SOL -> Wormhole -> Ethereum",
        "state_transitions": ["Instruction", "PostMessage", "Guardian", "VAA", "ERC20 Mint"],
        "detection_logic": [
            {"stage": "Instruction", "detection": "PostMessage -> VAA"},
            {"stage": "Ethereum", "detection": "ERC20 Mint"}
        ],
        "fingerprints": ["Wormhole Program", "Guardian Signature", "VAA", "Mint Event"],
        "identity_signals": ["VAA sequence", "Value Match", "Signature Correlation"],
        "confidence_scoring": {"VAA Match": 100, "Mint Event": 100, "Timing Match": 98}
    },
    {
        "scenario_id": "ETH_TORNADO_COINBASE",
        "chain": "Ethereum",
        "destination_chain": "Base",
        "category": "Mixer to CEX",
        "flow": "ETH -> Tornado -> Base -> Coinbase",
        "state_transitions": ["Deposit()", "Withdrawal()", "Relayer", "Bridge", "Base", "Coinbase"],
        "detection_logic": [
            {"stage": "Deposit()", "detection": "Tornado Cash Deposit"},
            {"stage": "Withdrawal()", "detection": "Tornado Cash Withdrawal via Relayer"},
            {"stage": "Bridge", "detection": "Bridge to Base"},
            {"stage": "Coinbase", "detection": "Coinbase Deposit on Base"}
        ],
        "fingerprints": ["Tornado Pool", "Withdrawal note", "Relayer", "Bridge Router", "Coinbase deposit"],
        "identity_signals": ["Timing clustering", "Value clustering", "Relayer fee subtraction"],
        "confidence_scoring": {"Deposit/Withdrawal Volume Match": 90, "Timing Correlation": 85, "CEX Cluster": 99}
    }
]

UNIVERSAL_MATRIX = {
    "Bitcoin": {"Lock": "Custodian", "Mint": "Custodian", "Burn": "Spend", "Transfer": "UTXO", "Bridge": "Custodian", "Exchange": "Deposit"},
    "Ethereum": {"Lock": "Lock()", "Mint": "Mint()", "Burn": "Burn()", "Transfer": "Transfer()", "Bridge": "Bridge Event", "Exchange": "Deposit"},
    "Solana": {"Lock": "Program", "Mint": "MintTo", "Burn": "Burn", "Transfer": "SPL Transfer", "Bridge": "CPI", "Exchange": "Deposit"},
    "TRON": {"Lock": "Contract", "Mint": "TRC20 Mint", "Burn": "Burn", "Transfer": "TRC20", "Bridge": "Internal Tx", "Exchange": "Deposit"},
    "XRP": {"Lock": "Escrow", "Mint": "Issued Asset", "Burn": "TrustLine", "Transfer": "Payment", "Bridge": "Memo", "Exchange": "Destination Tag"}
}

async def seed_ontology():
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        db = client[DB_NAME]
        col = db[COLLECTION_NAME]
        
        logger.info(f"Connected to MongoDB. Clearing '{COLLECTION_NAME}' collection...")
        await col.delete_many({})
        
        logger.info("Inserting Ontology Scenarios...")
        await col.insert_many(ONTOLOGY_DATA)
        
        logger.info("Inserting Universal Matrix...")
        await col.insert_one({"type": "UNIVERSAL_MATRIX", "data": UNIVERSAL_MATRIX})
        
        count = await col.count_documents({})
        logger.info(f"Seeding completed successfully! Total documents: {count}")
    except Exception as e:
        logger.error(f"Failed to seed ontology: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    asyncio.run(seed_ontology())
