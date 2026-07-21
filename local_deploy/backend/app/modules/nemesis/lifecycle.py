# NEMESIS Asset Lifecycle Engine
# Module: Asset Lifecycle Classification & Building

WRAPPED_ASSETS = {
    "BTC": ["WBTC", "renBTC", "sBTC", "tBTC", "BTCB", "WBTC.e"],
    "ETH": ["WETH", "stETH", "wstETH", "cbETH", "rETH"],
    "BNB": ["WBNB"],
    "AVAX": ["WAVAX"],
    "MATIC": ["WMATIC"],
    "SOL": ["wSOL"],
    "USDT": ["USDT.e", "axlUSDT"]
}

EVENT_TYPES = {
    "transfer",
    "swap",
    "mint",
    "burn",
    "bridge",
    "wrap",
    "unwrap",
    "deposit",
    "withdrawal",
    "mixer",
    "cex_deposit",
    "internal_tx",
    "nft_transfer"
}

def classify_event(tx):
    fn = (tx.get("functionName") or "").lower()
    inp = (tx.get("input") or "").lower()

    if "swap" in fn:
        return "swap"

    if "mint" in fn:
        return "mint"

    if "burn" in fn:
        return "burn"

    if "bridge" in fn:
        return "bridge"

    if "deposit" in fn and tx.get("entity_type") == "cex":
        return "cex_deposit"

    if "wrap" in fn:
        return "wrap"

    if "unwrap" in fn:
        return "unwrap"

    if tx.get("nft"):
        return "nft_transfer"

    return "transfer"

def build_asset_lifecycle(txs):
    lifecycle = []
    for tx in txs:
        lifecycle.append({
            "event": classify_event(tx),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "token_in": tx.get("token_in"),
            "token_out": tx.get("token_out"),
            "chain": tx.get("chain"),
            "entity_type": tx.get("entity_type", "unknown")
        })
    return lifecycle

def trace_wrapped_assets(path):
    traces = []
    for step in path:
        token_in = step.get("token_in")
        token_out = step.get("token_out")

        for native, wrappeds in WRAPPED_ASSETS.items():
            if token_out in wrappeds:
                traces.append({
                    "native": native,
                    "wrapped": token_out,
                    "event": step["event"]
                })
    return traces
