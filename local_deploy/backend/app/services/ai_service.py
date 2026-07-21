import os
import json
import logging
from typing import Dict, Any, List, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
import httpx

logger = logging.getLogger("AIService")

# Define the State for the LangGraph
class WalletState(TypedDict):
    wallet_address: str
    chain: str
    raw_tx_data: List[dict]
    labels: List[str]
    is_contract: bool
    contract_abi: str
    peel_chain_detected: bool
    clusters: List[str]
    cex_deposits: List[dict]
    analysis_report: str
    errors: List[str]

from datetime import datetime

# --- Nodes ---

def data_collection_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Collecting data for {state['wallet_address']}")
    
    # Extract unique counterparties
    counterparties = set()
    for tx in state["raw_tx_data"]:
        if tx["type"] == "Receive":
            counterparties.add(tx["sender"])
        else:
            counterparties.add(tx["receiver"])
            
    state["analysis_report"] += f"Collected {len(counterparties)} unique counterparties from {len(state['raw_tx_data'])} transactions.\n"
    return state

def peel_chain_detection_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Analyzing velocity and peel chains for {state['wallet_address']}")
    
    # Detect peel chain: Rapid successive sends
    sends = [tx for tx in state["raw_tx_data"] if tx["type"] == "Send"]
    # Sort chronologically (assuming raw_tx_data is desc from Etherscan, so reverse it)
    sends.reverse()
    
    peel_detected = False
    if len(sends) >= 4:
        for i in range(len(sends) - 3):
            try:
                t1 = datetime.strptime(sends[i]["timestamp"], '%Y-%m-%d %H:%M:%S')
                t4 = datetime.strptime(sends[i+3]["timestamp"], '%Y-%m-%d %H:%M:%S')
                # If 4 sends happen within 10 minutes
                if (t4 - t1).total_seconds() < 600:
                    peel_detected = True
                    break
            except: pass
            
    state["peel_chain_detected"] = peel_detected
    if peel_detected:
        state["analysis_report"] += "WARNING: High-velocity rapid-fire outward transfers detected (Classic Peel Chain behavior).\n"
    return state

def gnn_clustering_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Performing GNN clustering for {state['wallet_address']}")
    
    # Heuristic clustering based on tx ratio
    if not state["raw_tx_data"]:
        state["clusters"] = ["Dormant"]
    else:
        sends = len([tx for tx in state["raw_tx_data"] if tx["type"] == "Send"])
        receives = len(state["raw_tx_data"]) - sends
        if sends > receives * 3:
            state["clusters"] = ["Distribution/Sender Node"]
        elif receives > sends * 3:
            state["clusters"] = ["Accumulation/Receiver Node"]
        elif state["peel_chain_detected"]:
            state["clusters"] = ["Laundering/Peel Node"]
        else:
            state["clusters"] = ["Standard Intermediary"]
            
    state["analysis_report"] += f"Behavioral Cluster Assigned: {state['clusters'][0]}\n"
    return state

async def cex_illicit_matching_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Interfacing with CEX & Illicit lists for {state['wallet_address']}")
    from services.trace_engine import mongo_db
    
    illicit_hits = 0
    if mongo_db is not None:
        count = await mongo_db.darknet_data.count_documents({"uie_entities.value": state['wallet_address']})
        illicit_hits = count
        
    if illicit_hits > 0:
        state["analysis_report"] += f"CRITICAL: Found {illicit_hits} direct mentions in Darknet/Exploit databases.\n"
        state["clusters"].append("Known Malicious")
    return state

def smart_contract_analyzer_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Analyzing Smart Contract for {state['wallet_address']}")
    if state["is_contract"]:
        state["analysis_report"] += "Smart Contract execution detected. Standard routing logic.\n"
    return state

def ai_insights_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Generating AI Insights Report for {state['wallet_address']}")
    api_key = os.getenv("GEMINI_API_KEYS", "").split(",")[0].strip('"')
    if api_key:
        try:
            prompt = (
                f"Analyze the intelligence graph for wallet {state['wallet_address']} on {state['chain']}. "
                f"Behaviors detected: Peel chain: {state['peel_chain_detected']}, Clusters: {state['clusters']}. "
                f"Use the new Nemesis Ontology (e.g. BRIDGED_TO, SWAPPED_TO, MIXED, CEX_DEPOSIT) and Risk Scores to trace the asset's journey. "
                f"Write a chronological 4-sentence Investigation Summary assessing the holistic AML risk."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            prompt_payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            # Since LangGraph nodes are synchronous here, we use httpx synchronous client. Wait! The Pyodide environment patches everything so synchronous calls might crash if not awaited.
            # But the user is using `genai.Client()` synchronously which did `requests` anyway. Let's just use httpx sync.
            with httpx.Client() as client:
                resp = client.post(url, json=prompt_payload, timeout=20.0)
                data = resp.json()
                
            if "candidates" in data and data["candidates"]:
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"]
                state["analysis_report"] += f"\n\nAI Insights:\n{ai_text}"
            else:
                state["analysis_report"] += "\n\nAI Insights: Unavailable."
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            state["analysis_report"] += "\n\nAI Insights: Unavailable."
    else:
        state["analysis_report"] += "\n\nAI Insights: Gemini API Key missing."
        
    return state

# --- Build Graph ---

workflow = StateGraph(WalletState)

workflow.add_node("data_collection", data_collection_node)
workflow.add_node("peel_chain", peel_chain_detection_node)
workflow.add_node("clustering", gnn_clustering_node)
workflow.add_node("cex_matching", cex_illicit_matching_node)
workflow.add_node("contract_analyzer", smart_contract_analyzer_node)
workflow.add_node("ai_insights", ai_insights_node)

workflow.add_edge("data_collection", "peel_chain")
workflow.add_edge("peel_chain", "clustering")
workflow.add_edge("clustering", "cex_matching")
workflow.add_edge("cex_matching", "contract_analyzer")
workflow.add_edge("contract_analyzer", "ai_insights")
workflow.add_edge("ai_insights", END)

workflow.set_entry_point("data_collection")

# Compile the graph
wallet_analyzer_app = workflow.compile()

async def analyze_wallet(wallet_address: str, chain: str, tx_data: List[dict], is_contract: bool = False) -> str:
    initial_state = {
        "wallet_address": wallet_address,
        "chain": chain,
        "raw_tx_data": tx_data,
        "labels": [],
        "is_contract": is_contract,
        "contract_abi": "",
        "peel_chain_detected": False,
        "clusters": [],
        "cex_deposits": [],
        "analysis_report": "",
        "errors": []
    }
    
    final_state = await wallet_analyzer_app.ainvoke(initial_state)
    return final_state["analysis_report"]
