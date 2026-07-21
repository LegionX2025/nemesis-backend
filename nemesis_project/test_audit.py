import urllib.request
import urllib.error
import json
import logging
import os
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NemesisAudit")

def load_env():
    """Manual dotenv loader to avoid requiring python-dotenv"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Could not load .env file manually: {e}")

load_env()

# Test addresses provided by user
ADDRESSES = {
    "BITCOIN": [
        "bc1qguj54d66l502pwvft3zjrgwtmvhhq88nsaj7t6"
    ],
    "ETHEREUM": [
        "0x2a91386cEdb02D0d1fc37a262B07d458A015F06F",
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "0xD6094943979AfB5d2748FBB84788Aa4D2b0bd857",
        "0x69F8c4c19A3Fb24859fc9E0DacfD554c17958d75",
        "0x4Cbcff095bdb49885439c4B4F3c8dEC287F942d2"
    ],
    "XRP": [
        "rJnLjofJ25FQc5wXgac4LCJFC364hptbJx",
        "rhwTCnnXrunzYGAe9GVEqcbUx7PUbTHWsm"
    ]
}

def sync_bitquery_fetch(network, query, variables, api_key):
    if network == "bitcoin":
        url = "https://graphql.bitquery.io"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
            "Authorization": f"Bearer {api_key}"
        }
    else:
        url = "https://streaming.bitquery.io/graphql"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    payload = json.dumps({"query": query, "variables": variables}).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data
            else:
                logger.error(f"HTTP Error {response.status}")
                return None
    except urllib.error.URLError as e:
        logger.error(f"Bitquery fetch failed: {e}")
        return None

def audit_bitquery():
    logger.info("--- AUDIT: Bitquery V2 Synchronous Fetch ---")
    
    api_key = os.environ.get("BITQUERY_V2_TOKEN") or os.environ.get("BITQUERY_API_TOKEN")
    
    if not api_key:
        logger.error("Bitquery API key is missing! Please ensure BITQUERY_V2_TOKEN or BITQUERY_API_TOKEN is set in .env")
        return False
        
    logger.info(f"Using Bitquery API Key: {api_key[:5]}...{api_key[-5:]}")
    
    # 1. Test EVM (Ethereum)
    eth_addr = ADDRESSES["ETHEREUM"][0]
    logger.info(f"Testing EVM fetch for: {eth_addr}")
    evm_query = """
    query ($network: evm_network, $address: String, $limit: Int) {
      EVM(network: $network, dataset: realtime) {
        Transfers(
          where: {any: [{Transfer: {Sender: {is: $address}}}, {Transfer: {Receiver: {is: $address}}}]}
          limit: {count: $limit}
          orderBy: {descending: Block_Time}
        ) {
          Transaction { Hash }
          Transfer { Sender Receiver Amount Currency { Symbol } }
        }
      }
    }
    """
    evm_data = sync_bitquery_fetch("eth", evm_query, {"network": "eth", "address": eth_addr.lower(), "limit": 2}, api_key)
    if evm_data:
        if "errors" in evm_data:
            logger.error(f"Bitquery EVM errors: {json.dumps(evm_data['errors'])}")
        
        data_block = evm_data.get("data") or {}
        evm_block = data_block.get("EVM") or {}
        transfers = evm_block.get("Transfers") or []
        
        logger.info(f"EVM Success! Found {len(transfers)} transfers.")
        if transfers:
            logger.info(json.dumps(transfers[0], indent=2))
            
    # 2. Test UTXO (Bitcoin)
    btc_addr = ADDRESSES["BITCOIN"][0]
    logger.info(f"\nTesting UTXO (Bitcoin) fetch for: {btc_addr}")
    btc_query = """
    query ($address: String, $limit: Int) {
      bitcoin {
        inputs(
          inputAddress: {is: $address}
          options: {limit: $limit}
        ) {
          transaction { hash }
          value
        }
      }
    }
    """
    btc_data = sync_bitquery_fetch("bitcoin", btc_query, {"address": btc_addr, "limit": 2}, api_key)
    if btc_data:
        if "errors" in btc_data:
            logger.error(f"Bitquery BTC errors: {json.dumps(btc_data['errors'])}")
            
        data_block = btc_data.get("data") or {}
        btc_block = data_block.get("bitcoin") or {}
        inputs = btc_block.get("inputs") or []
        
        logger.info(f"Bitcoin Success! Found {len(inputs)} input transactions.")
        if inputs:
            logger.info(json.dumps(inputs[0], indent=2))

def run_full_audit():
    logger.info("=========================================")
    logger.info(" NEMESIS TRACER - NO-DEPENDENCY AUDIT ")
    logger.info("=========================================")
    
    audit_bitquery()
    
    logger.info("=========================================")
    logger.info(" NEMESIS TRACER - AUDIT COMPLETE")
    logger.info("=========================================")

if __name__ == "__main__":
    run_full_audit()
