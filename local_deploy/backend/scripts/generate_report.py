import os
import sys
import json
import uuid
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_llm_response(prompt: str, trace_data: list = None) -> str:
    """Uses Gemini to generate rich text if available. Fails gracefully otherwise."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Inject trace context into the prompt for the actual LLM
    context_prompt = prompt
    if trace_data:
        context_prompt += f"\n\nHere is the raw trace data for context:\n{json.dumps(trace_data[:10], indent=2)}"
        
    if HAS_GENAI and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(context_prompt)
            return response.text.replace("\n", "<br>")
        except Exception as e:
            print(f"[!] LLM Generation failed: {e}")
            return "<strong style='color:red;'>[DATA INCOMPLETE] LLM Service Unavailable. Trace data extraction pending manual analyst review.</strong>"
    return "<strong style='color:red;'>[DATA INCOMPLETE] API Key Missing or Service Offline.</strong>"

def prepare_graph_data(trace_data):
    nodes = []
    edges = []
    added_nodes = set()
    
    for edge in trace_data:
        fr = edge['From Wallet(Entity)']
        to = edge['To Wallet(Entity)']
        
        fr_id = fr.split(" ")[0]
        to_id = to.split(" ")[0]
        
        # Color nodes based on tags
        def get_color(entity_str):
            s = entity_str.upper()
            if "VICTIM" in s: return {"background": "#ffffff", "border": "#d88e00"}
            if "CEX" in s or "EXCHANGE" in s or "BINANCE" in s: return {"background": "#e8f5e9", "border": "#2e7d32"}
            if "MIX" in s: return {"background": "#ffffff", "border": "#1976d2"}
            return {"background": "#ffffff", "border": "#b71c1c"}

        if fr_id not in added_nodes:
            nodes.append({"id": fr_id, "label": f"{fr_id[:8]}...\n({edge.get('Type of Tx Correlation', 'Seed')})", "color": get_color(fr)})
            added_nodes.add(fr_id)
        if to_id not in added_nodes:
            nodes.append({"id": to_id, "label": f"{to_id[:8]}...\n({edge.get('To Receiver Entity', 'Node')})", "color": get_color(to)})
            added_nodes.add(to_id)
            
        edges.append({
            "from": fr_id, 
            "to": to_id, 
            "label": f"{edge.get('Amount', '')}\nTx: {edge.get('TX Hash', '')[:8]}...",
            "font": {"align": "middle"}
        })
        
    return json.dumps(nodes), json.dumps(edges)

def generate():
    print("[+] Initializing Lionsgate Forensic Report Generator (AB_CASE_1 Layout)...")
    
    trace_file = os.path.join(os.path.dirname(__file__), "..", "..", "custom_trace_report.json")
    if not os.path.exists(trace_file):
        print(f"[!] Error: Trace data not found.")
        sys.exit(1)
        
    with open(trace_file, "r") as f:
        trace_data = json.load(f)
        
    if not trace_data: sys.exit(1)
    
    first_edge = trace_data[0]
    target_asset = first_edge['Tx Attributions'].split("|")[0].replace("Asset:", "").strip()
    
    # Extract unique seeds
    seeds = set()
    for e in trace_data:
        seeds.add(e['From Wallet(Entity)'].split(" ")[0])
        if len(seeds) > 2: break
        
    suspect_wallet_list = "<br>".join(list(seeds))
    
    # Calculate Terminal logic
    terminal_cex_dict = {}
    for e in trace_data:
        to_addr = e['To Wallet(Entity)'].split(" ")[0]
        to_entity = e['To Receiver Entity'].upper()
        if "CEX" in to_entity or "EXCHANGE" in to_entity or "BINANCE" in to_entity or "KRAKEN" in to_entity:
            amt = float(str(e['Amount']).split(" ")[0].replace(",", ""))
            if to_addr not in terminal_cex_dict:
                terminal_cex_dict[to_addr] = {"amount": 0.0, "name": to_entity}
            terminal_cex_dict[to_addr]["amount"] += amt

    # Dynamic Flow Diagrams
    flow_steps_html = ""
    for i, edge in enumerate(trace_data):
        fr_addr = edge['From Wallet(Entity)'].split(" ")[0]
        to_addr = edge['To Wallet(Entity)'].split(" ")[0]
        amt = edge['Amount']
        tx = edge['TX Hash']
        date = edge['Date/Time (UTC)']
        
        to_entity = edge['To Receiver Entity']
        
        # Determine step type
        step_class = "type-suspect"
        step_title = "Suspect Hop"
        if "MIX" in edge['Type of Tx Correlation'].upper() or "HOP" in edge['Type of Tx Correlation'].upper():
            step_class = "type-mixing"
            step_title = "Mixing Node"
        if "CEX" in to_entity.upper() or "EXCHANGE" in to_entity.upper():
            step_class = "type-cex"
            step_title = "CEX Deposit"
        if i == 0:
            step_class = "type-victim"
            step_title = "Origin Victim Drain"

        flow_steps_html += f"""
        <h3>{i+1}. FLOW TRANSITION: {fr_addr[:8]}... to {to_addr[:8]}...</h3>
        <table class="data-table">
            <tr><th>Date (UTC)</th><th>Transaction Hash (TxID)</th><th>From Entity / Address</th><th>To Suspect Address</th><th>Amount</th></tr>
            <tr>
                <td>{date}</td>
                <td>{tx}</td>
                <td>{fr_addr}</td>
                <td>{to_addr}</td>
                <td>{amt}</td>
            </tr>
        </table>
        
        <div class="flow-container">
            <div class="node-box {step_class if i==0 else 'type-mixing'}">
                <div class="node-title">SOURCE NODE</div>
                <div class="node-address">{fr_addr}</div>
            </div>
            
            <div class="tx-arrow">
                <div class="tx-details">Tx: {tx}<br><span class="tx-amount">Amount: {amt}</span></div>
                <div class="arrow-line"></div>
            </div>
            
            <div class="node-box {step_class}">
                <div class="node-title">{step_title}</div>
                <div class="node-entity">{to_entity}</div>
                <div class="node-address">{to_addr}</div>
            </div>
        </div>
        """

    # Terminal Target HTML
    terminal_target_html = ""
    if terminal_cex_dict:
        terminal_target_html += "<div class='terminal-container'>"
        for addr, data in terminal_cex_dict.items():
            terminal_target_html += f"""
            <div class='terminal-target'>
                <div class='terminal-header'>TERMINAL TARGET</div>
                <div class='node-entity'>Entity: {data['name']} (VASP Offramp)</div>
                <div style='font-weight:bold; margin-top:10px;'>Known Centralized Exchange Deposit Address</div>
                <div class='node-address' style='font-size:12pt; padding:15px; margin: 15px 0;'>{addr}</div>
                <div style='color:var(--cex-color); font-weight:bold;'>Total Funds Landed: {data['amount']} {target_asset}</div>
                <div class='terminal-sub'>TARGET FOR IMMEDIATE SUBPOENA</div>
            </div>
            """
        terminal_target_html += "</div>"
    else:
        terminal_target_html = "<div class='terminal-container'><h3>No Terminal CEX Identified Yet.</h3></div>"

    graph_nodes, graph_edges = prepare_graph_data(trace_data)
    
    print("[+] Synthesizing Tier 3 Analyst narratives via LLM...")
    prompt_base = f"Act as a Blockchain Forensics Analyst for Lionsgate Network. "
    narrative_html = get_llm_response(prompt_base + "Write the 'EVIDENTIARY TRACE NARRATIVE FOR MOTIONS / WARRANTS'. Focus on AI matching, fragmentation, mixing, and convergence to CEX endpoints with high confidence. Keep it to 2 solid paragraphs. Do not use generic templates or mock entities, reference the specific wallets and amounts in the provided trace data.", trace_data)
    osint_report = get_llm_response(prompt_base + "Write the OSINT Threat Intelligence Report detailing behavioral analysis and actor profiling. Extract insights exclusively from the provided trace data without generating mock personas.", trace_data)
    graph_narrative_html = get_llm_response(prompt_base + "Write the 'EVIDENTIARY SUMMARY: AI-DRIVEN RECOMBINATION TRACING' detailing the complete unredacted chain of custody, AI confidence factors in identifying terminal consolidation wallets, and how the assets converged. Do not use mock names like CALEO. Rely completely on the trace data and frame it as solid evidentiary proof for seizure motions.", trace_data)

    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('forensic_report.html')
    # Encode logo.jpeg to base64 to embed in the HTML
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logo.jpeg"))
    logo_base64 = ""
    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            logo_base64 = f"data:image/jpeg;base64,{encoded_string}"
    
    html_output = template.render(
        case_id=str(uuid.uuid4()).upper()[:8],
        suspect_wallet_list=suspect_wallet_list,
        target_asset=target_asset,
        target_amount=trace_data[0]['Amount'] if trace_data else "Unknown",
        date_execution=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        narrative_html=narrative_html,
        graph_narrative_html=graph_narrative_html,
        flow_steps_html=flow_steps_html,
        terminal_target_html=terminal_target_html,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        osint_report=osint_report,
        file_path="Lionsgate_Forensic_Report.pdf",
        total_pages="5",
        logo_base64=logo_base64
    )
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Lionsgate_Forensic_Report.html"))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"\n[SUCCESS] Forensic Report (AB_CASE_1 Design) generated successfully at:\n{output_path}")

if __name__ == "__main__":
    generate()
