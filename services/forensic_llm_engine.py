import logging
import json
import os
from typing import Dict, Any, List
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("OmniChainEngine.ForensicLLM")

# Initialize Gemini if key exists
raw_keys = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEY = None
for k in raw_keys.split(','):
    k = k.strip().strip('"')
    if k.startswith("AIza"):
        GEMINI_API_KEY = k
        break

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiForensicEngine:
    def __init__(self):
        # We only instantiate the client if configured
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY and genai else None
        self.cache = {}

    async def process(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full forensic classification pipeline
        """
        # 1. Rule-based fast path 
        rule_result = tx.get("edge_type", tx.get("action", "UNKNOWN"))

        # 2. If uncertain -> LLM reasoning layer
        # For cost/speed, we only invoke this if rule_result is ambiguous/TRANSFER and model is loaded
        if rule_result in ["UNKNOWN", None, "TRANSFER", "NATIVE_TRANSFER"] and self.client:
            llm_result = await self._llm_analyze(tx)
            merged = self._merge(rule_result, llm_result)
        else:
            merged = {
                "final_type": rule_result,
                "confidence": 0.9 if rule_result != "UNKNOWN" else 0.5,
                "reasoning": "Rule-based deterministic classification",
                "cross_chain_path": []
            }

        # 3. enrich with cross-chain inference
        enriched = self._enrich_context(tx, merged)
        return enriched

    async def _llm_analyze(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = tx.get("hash")
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]

        prompt = self.build_prompt(tx)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _generate():
                return self.client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=prompt
                )
                
            response = await loop.run_in_executor(None, _generate)
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            result = json.loads(text.strip())
            
            if cache_key:
                self.cache[cache_key] = result
                
            return result
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"type": "UNKNOWN", "confidence": 0.5, "reasoning": f"LLM Error: {e}", "path": []}

    def build_prompt(self, tx: Dict[str, Any]) -> str:
        return f"""
Analyze this blockchain transaction and infer the underlying intent.

Chain: {tx.get("chain", "UNKNOWN")}
From: {tx.get("from", "UNKNOWN")}
To: {tx.get("to", "UNKNOWN")}
Value: {tx.get("value", "UNKNOWN")} {tx.get("tokenSymbol", "")}
Input: {tx.get("input", "0x")[:500]} 

Classify into exactly one of these types:
TRANSFER, SWAP, BRIDGE, MINT, BURN, MIXER, CEX_DEPOSIT, CEX_WITHDRAWAL, WRAP, UNWRAP, DEX, DEFI, DAPP

Based on CROSS-CHAIN FORENSIC RULES:
- TRANSFER: simple value movement
- SWAP: DEX router signatures, token changes
- BRIDGE: lock -> mint symmetry, custody deposit
- MINT / BURN: asset creation/destruction
- MIXER: Tornado Cash, CoinJoin, layered obfuscation
- CEX_DEPOSIT / CEX_WITHDRAWAL: known exchange clusters, batched outflows
- WRAP / UNWRAP: native to wrapped representation

Return ONLY a valid JSON object matching this schema:
{{
    "type": "CLASSIFICATION_TYPE",
    "confidence": 0.9,
    "reasoning": "Explain why this transaction fits the classification and the inferred intent.",
    "path": ["TRANSFER", "SWAP", "MIXER"]
}}
"""

    def _merge(self, rule: str, llm: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "final_type": llm.get("type", rule),
            "confidence": llm.get("confidence", 0.8),
            "reasoning": llm.get("reasoning", ""),
            "cross_chain_path": llm.get("path", [])
        }

    def _enrich_context(self, tx: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **classification,
            "chain": tx.get("chain"),
            "wallet_role": self._detect_role(tx),
            "graph_edges": self._build_edges(tx, classification)
        }

    def _detect_role(self, tx: Dict[str, Any]) -> str:
        to_addr = str(tx.get("to", "")).lower()
        input_data = str(tx.get("input", "")).lower()
        
        if "binance" in to_addr or "0x28c6c06298d514db089934071355e5743bf21d60" in to_addr:
            return "CEX"
        if "swap" in input_data or "router" in input_data:
            return "DEX"
        return "EOA"

    def _build_edges(self, tx: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "src": tx.get("from"),
            "dst": tx.get("to"),
            "type": classification.get("final_type", "TRANSFER"),
            "chain": tx.get("chain"),
            "value": tx.get("value"),
            "timestamp": tx.get("timeStamp")
        }


class FlowReconstructor:
    def reconstruct(self, tx_graph: List[Dict[str, Any]]) -> str:
        """
        Builds full laundering / movement path sequence as a string
        """
        paths = []
        for tx in tx_graph:
            path = {
                "start": tx.get("from"),
                "end": tx.get("to"),
                "chain": tx.get("chain"),
                "step_type": tx.get("type") or tx.get("edge_type", "TRANSFER")
            }
            paths.append(path)
            
        return self._compress_paths(paths)

    def _compress_paths(self, paths: List[Dict[str, Any]]) -> str:
        """
        Example: TRANSFER → SWAP → BRIDGE → MIXER → CEX
        """
        current = []
        for p in paths:
            step = p.get("step_type", "UNKNOWN")
            if not current or current[-1] != step:
                current.append(step)
                
        return " → ".join(current)
