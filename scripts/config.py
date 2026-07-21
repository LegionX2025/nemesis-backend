import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URL = os.getenv("DATABASE_MONGO_URL")
    POSTGRES_URI = os.getenv("POSTGRES_URI")
    APP_MODE = os.getenv("APP_MODE", "ENTERPRISE_GOVERNMENT")
    
    INFURA_KEYS = [os.getenv("INFURA_API_KEY")]
    INFURA_ETH = os.getenv("INFURA_ETHEREUM_MAINNET")
    
    GETBLOCK_BTC = os.getenv("GETBLOCK_BTC_KEY")
    PUBLICNODE_BTC = os.getenv("PUBLICNODE_BITCOIN_RPC")
    
    TATUM_KEY = os.getenv("TATUM_API_KEY")
    GEMINI_KEYS = os.getenv("GEMINI_API_KEYS", "").split(",")
    AI_MODEL_ORDER = os.getenv("AI_MODEL_ORDER", "").split(",")
