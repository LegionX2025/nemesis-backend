import requests
import json
import os
import re

class TransactionAnalyzer:
    def __init__(self):
        # Fallback to public endpoints if env vars are missing
        self.eth_rpc = os.getenv('INFURA_ETHEREUM_MAINNET', 'https://cloudflare-eth.com')
        self.btc_rpc = os.getenv('PUBLICNODE_BITCOIN_RPC', 'https://bitcoin-rpc.publicnode.com')
        self.bsc_rpc = os.getenv('INFURA_BSC_MAINNET', 'https://bsc-dataseed.binance.org')
        self.polygon_rpc = os.getenv('INFURA_POLYGON_MAINNET', 'https://polygon-rpc.com')

    def analyze(self, tx_hash: str):
        # Heuristics for chain detection
        tx_hash = tx_hash.strip()
        
        # Solana (88 chars base58)
        if re.match(r'^[1-9A-HJ-NP-Za-km-z]{88}$', tx_hash):
            return self._analyze_solana(tx_hash)
            
        # EVM / BTC / TRX (64 hex chars)
        if re.match(r'^(0x)?[a-fA-F0-9]{64}$', tx_hash):
            hash_clean = tx_hash if tx_hash.startswith('0x') else '0x' + tx_hash
            
            # 1. Try Ethereum
            eth_res = self._analyze_evm(hash_clean, self.eth_rpc, "ETH", "ETH")
            if eth_res['success']: return eth_res
            
            # 2. Try BSC
            bsc_res = self._analyze_evm(hash_clean, self.bsc_rpc, "BSC", "BNB")
            if bsc_res['success']: return bsc_res
            
            # 3. Try Polygon
            poly_res = self._analyze_evm(hash_clean, self.polygon_rpc, "POLYGON", "MATIC")
            if poly_res['success']: return poly_res
            
            # 4. Try Bitcoin (needs hex without 0x)
            btc_hash = tx_hash.replace('0x', '')
            btc_res = self._analyze_btc(btc_hash)
            if bsc_res['success']: return btc_res
            
        return {"success": False, "error": "Transaction not found on supported chains or invalid hash format."}

    def _analyze_evm(self, tx_hash: str, rpc_url: str, network: str, native_currency: str):
        try:
            payload = {"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":[tx_hash],"id":1}
            r = requests.post(rpc_url, json=payload, timeout=5)
            data = r.json()
            
            if 'result' in data and data['result'] is not None:
                tx = data['result']
                
                # Known Bridges Mapping (Lowercase)
                known_bridges = {
                    "0x8731d54e9d02c286767d56ac03e8037c07e01e98": "Stargate Router",
                    "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae": "Multichain/AnySwap Router",
                    "0x2796317b0ff8538f253012862c06787adfb8ceb6": "Synapse Bridge",
                    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "Polygon PoS Bridge"
                }
                
                contract_interacted = (tx.get('to') or "").lower()
                bridge_info = None
                if contract_interacted in known_bridges:
                    bridge_info = known_bridges[contract_interacted]
                
                max_amount = 0
                max_currency = native_currency
                target_address = tx.get('to', '')
                
                # Check for native value transfer
                value_wei = int(tx.get('value', '0x0'), 16)
                if value_wei > 0:
                    max_amount = value_wei / (10**18)
                
                # Check receipts for ERC20 transfers
                receipt_payload = {"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params":[tx_hash],"id":1}
                rr = requests.post(rpc_url, json=receipt_payload, timeout=5)
                r_data = rr.json()
                
                if 'result' in r_data and r_data['result'] is not None:
                    logs = r_data['result'].get('logs', [])
                    # Find Transfer event: Transfer(address indexed from, address indexed to, uint256 value)
                    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                    
                    for log in logs:
                        topics = log.get('topics', [])
                        if len(topics) >= 3 and topics[0] == transfer_topic:
                            to_addr = "0x" + topics[2][26:]
                            raw_val = int(log.get('data', '0x0'), 16)
                            
                            token_addr = log.get('address', '').lower()
                            currency = "TOKEN"
                            decimals = 18
                            
                            if token_addr in ['0xdac17f958d2ee523a2206206994597c13d831ec7', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48']:
                                currency = "USDT" if "dac" in token_addr else "USDC"
                                decimals = 6
                                
                            amount = raw_val / (10**decimals)
                            
                            # Update max amount logic (handling DEX swaps where token output > native input logic)
                            if amount > max_amount or (amount > 0 and max_amount == 0):
                                max_amount = amount
                                max_currency = currency
                                target_address = to_addr
                                
                if max_amount > 0 or bridge_info:
                    return {
                        "success": True,
                        "network": network,
                        "currency": max_currency,
                        "total_loss": max_amount,
                        "target_address": target_address,
                        "cross_chain_bridge": bridge_info
                    }
                    
                return {"success": False, "error": "No value transfer found."}
            return {"success": False, "error": "Transaction not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_btc(self, tx_hash: str):
        # Use blockchain.info as a simple public fallback for BTC since RPC requires auth/complex setup
        try:
            r = requests.get(f"https://blockchain.info/rawtx/{tx_hash}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                
                # Heuristic: the largest output that isn't returning to an input address is the target
                inputs = [inp.get('prev_out', {}).get('addr') for inp in data.get('inputs', [])]
                
                max_out = 0
                target = ""
                for out in data.get('out', []):
                    addr = out.get('addr')
                    val = out.get('value', 0)
                    if addr not in inputs and val > max_out:
                        max_out = val
                        target = addr
                
                if max_out > 0:
                    return {
                        "success": True,
                        "network": "BTC",
                        "currency": "BTC",
                        "total_loss": max_out / 100000000, # satoshis to BTC
                        "target_address": target
                    }
            return {"success": False}
        except:
            return {"success": False}

    def _analyze_solana(self, tx_hash: str):
        # Stub for Solana, returning generic to let frontend handle it gracefully
        return {
            "success": True,
            "network": "SOL",
            "currency": "SOL",
            "total_loss": 0,
            "target_address": "Requires SOL RPC"
        }
