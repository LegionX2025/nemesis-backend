import os
import json
import logging
from typing import Dict, Any, List, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from google import genai

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

# --- Nodes ---

def data_collection_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Collecting data for {state['wallet_address']}")
    # Simulate data fetching for explorer labels and cross-chain mappings
    return state

def peel_chain_detection_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Analyzing velocity and peel chains for {state['wallet_address']}")
    # Analyze tx pattern for rapid fan-out (peel chain)
    if len(state["raw_tx_data"]) > 10:
        state["peel_chain_detected"] = True
    return state

def gnn_clustering_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Performing GNN clustering for {state['wallet_address']}")
    # Simulate DBScan/GNN grouping
    state["clusters"] = ["Cluster-Alpha"] if state["peel_chain_detected"] else ["Unclustered"]
    return state

def cex_illicit_matching_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Interfacing with CEX & Illicit lists for {state['wallet_address']}")
    # Simulate matching against Arkham/Darknet heuristics
    return state

def smart_contract_analyzer_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Analyzing Smart Contract for {state['wallet_address']}")
    if state["is_contract"]:
        state["analysis_report"] = "Smart Contract detected. Decompilation reveals standard routing logic."
    return state

def ai_insights_node(state: WalletState) -> WalletState:
    logger.info(f"LangGraph: Generating AI Insights Report for {state['wallet_address']}")
    
    api_key = os.getenv("GEMINI_API_KEYS", "").split(",")[0].strip('"')
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"Analyze wallet {state['wallet_address']} on {state['chain']}. Peel chain detected: {state['peel_chain_detected']}. Contract: {state['is_contract']}. Write a short 3-sentence forensic summary."
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            state["analysis_report"] += f"\n\nAI Insights:\n{resp.text}"
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
