import os
import re

def mask_token(token: str) -> str:
    if not token or len(token) < 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"

def get_endpoint_for_provider(key_name: str) -> str:
    key_name = key_name.upper()
    
    if "BITQUERY" in key_name:
        return "https://streaming.bitquery.io/graphql (Docs: https://docs.bitquery.io/docs/authorisation/how-to-generate/)"
    elif "ETHERSCAN" in key_name:
        return "https://api.etherscan.io/api"
    elif "POLYGONSCAN" in key_name:
        return "https://api.polygonscan.com/api"
    elif "BSCSCAN" in key_name:
        return "https://api.bscscan.com/api"
    elif "ARBISCAN" in key_name:
        return "https://api.arbiscan.io/api"
    elif "OPTIMISM" in key_name:
        return "https://api-optimistic.etherscan.io/api"
    elif "BASESCAN" in key_name:
        return "https://api.basescan.org/api"
    elif "SNOWTRACE" in key_name:
        return "https://api.snowtrace.io/api"
    elif "GETBLOCK" in key_name:
        return "https://go.getblock.io/<TOKEN>/"
    elif "TOKENVIEW" in key_name:
        return "https://usdt.tokenview.io/api/"
    elif "OKLINK" in key_name:
        return "https://www.oklink.com/api/v5/explorer/"
    elif "ETHPLORER" in key_name:
        return "https://ethplorer.io/search/"
    elif "TATUM" in key_name:
        return "https://api.tatum.io/v3/"
    elif "ANKR" in key_name:
        return "https://rpc.ankr.com/multichain/<TOKEN>"
    elif "INFURA" in key_name:
        return "https://mainnet.infura.io/v3/<TOKEN>"
    elif "PUBLICNODE" in key_name:
        if "WSS" in key_name:
            return "wss://*.publicnode.com"
        return "https://*.publicnode.com"
    elif "XRPSCAN" in key_name:
        return "https://api.xrpscan.com/api/v1"
    elif "GEMINI" in key_name:
        return "https://generativelanguage.googleapis.com/v1beta/models/"
    elif "AIML" in key_name:
        return "https://api.aimlapi.com/"
    elif "NEO4J" in key_name:
        return "neo4j+s://*.databases.neo4j.io"
    
    return "Custom/Internal Endpoint"

def auto_index_providers(env_path: str = "../.env"):
    providers = []
    
    if not os.path.exists(env_path):
        return providers
        
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                
                # Check if it's an API Key, Token, RPC, or URI
                if any(suffix in key for suffix in ["_KEY", "_TOKEN", "_RPC", "_WSS", "_URI", "_URL"]):
                    # Ignore pure DB URLs to avoid leaking passwords in this view, except NEO4J URI
                    if ("DATABASE" in key or "MONGO" in key) and "NEO4J" not in key:
                        continue
                        
                    provider_type = "API Key"
                    if "TOKEN" in key:
                        provider_type = "Bearer Token"
                    elif "RPC" in key:
                        provider_type = "RPC Node"
                    elif "WSS" in key:
                        provider_type = "WebSocket"
                        
                    providers.append({
                        "name": key,
                        "type": provider_type,
                        "masked_key": mask_token(val),
                        "endpoint": get_endpoint_for_provider(key),
                        "status": "Active" if val else "Missing"
                    })
    except Exception as e:
        print(f"Error parsing .env for API providers: {e}")
        
    return providers
