from enum import Enum

class WalletCategory(str, Enum):
    PERSONAL = "Personal Wallets (EOA)"
    CEX = "Centralized Exchange (CEX)"
    CUSTODY = "Custody Providers"
    DEX = "Decentralized Exchange (DEX)"
    DEFI = "DeFi Protocol"
    BRIDGE = "Cross-Chain Bridge"
    MEV = "MEV & Arbitrage"
    ILLICIT = "Illicit Activity"
    MIXER = "Mixer & Privacy"
    MINING = "Mining & Validation"
    GAMING = "Gaming & Metaverse"
    NFT = "NFT & Web3 Social"
    SYSTEM = "System & Infrastructure"
    UNKNOWN = "Unknown"

class WalletClassification(str, Enum):
    # 1. Personal Wallets
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
    MULTI_SIGNATURE = "Multi-Signature Wallet"
    SMART_ACCOUNT = "Smart Account (ERC-4337)"

    # 2. Centralized Exchange (CEX)
    CEX_DEPOSIT = "Exchange Deposit Wallet"
    CEX_WITHDRAWAL = "Exchange Withdrawal Wallet"
    CEX_HOT = "Exchange Hot Wallet"
    CEX_COLD = "Exchange Cold Wallet"
    CEX_TREASURY = "Exchange Treasury"
    CEX_OPERATIONS = "Exchange Operations"
    CEX_FEE = "Exchange Fee Wallet"
    CEX_LIQUIDITY = "Exchange Liquidity Wallet"
    CEX_CUSTODIAN = "Exchange Custodian"
    CEX_INTERNAL = "Exchange Internal Wallet"

    # 3. Custody Providers
    INSTITUTIONAL_CUSTODIAN = "Institutional Custodian"
    QUALIFIED_CUSTODIAN = "Qualified Custodian"
    MPC_WALLET = "MPC Wallet"
    ENTERPRISE_TREASURY = "Enterprise Treasury"
    ASSET_CUSTODIAN = "Asset Custodian"

    # 4. DeFi & DEX
    DEX_ROUTER = "DEX Router"
    DEX_POOL = "DEX Liquidity Pool"
    DEFI_VAULT = "DeFi Yield Vault"
    DEFI_STAKING = "Staking Contract"
    LENDING_POOL = "Lending Protocol Pool"
    FLASH_LOAN = "Flash Loan Contract"
    
    # 5. Bridges
    BRIDGE_LOCKUP = "Bridge Lockup Contract"
    BRIDGE_RELAYER = "Bridge Relayer"
    CROSS_CHAIN_ROUTER = "Cross-Chain Router"

    # 6. MEV & Arbitrage
    MEV_BOT = "MEV Bot"
    ARBITRAGE_BOT = "Arbitrage Bot"
    SANDWICH_BOT = "Sandwich Bot"
    SNIPER_BOT = "Sniper Bot"
    FRONT_RUNNER = "Front-Runner Bot"

    # 7. Illicit & High Risk
    HACKER = "Hacker / Exploiter"
    SCAMMER = "Scammer / Phisher"
    RANSOMWARE = "Ransomware Operator"
    DARKNET_MARKET = "Darknet Market"
    TERRORIST_FINANCING = "Terrorist Financing"
    SANCTIONED = "Sanctioned Entity (OFAC)"
    STOLEN_FUNDS = "Stolen Funds Repository"

    # 8. Privacy & Mixers
    MIXER = "Mixer Protocol"
    COINJOIN = "CoinJoin Coordinator"
    PRIVACY_ROUTER = "Privacy Router"

    # 9. Mining
    MINER = "Miner / Validator"
    MINING_POOL = "Mining Pool"
    BLOCK_BUILDER = "Block Builder"

    # Catch-all
    UNCLASSIFIED = "Unclassified"

def get_category_for_classification(classification: WalletClassification) -> WalletCategory:
    """Helper method to map a classification back to its parent category."""
    mapping = {
        WalletClassification.PERSONAL_WALLET: WalletCategory.PERSONAL,
        WalletClassification.WHALE: WalletCategory.PERSONAL,
        WalletClassification.CEX_HOT: WalletCategory.CEX,
        WalletClassification.HACKER: WalletCategory.ILLICIT,
        # (Additional mappings would be loaded dynamically from DB or GBIO)
    }
    return mapping.get(classification, WalletCategory.UNKNOWN)
