import os
import re

source_html_path = r"C:\Users\LEGIONX\Downloads\nemesis_enterprise_dashboard (1).html"
target_html_path = r"C:\Users\LEGIONX\Downloads\cases\nemesis_project\templates\nemesis_tracer.html"

with open(source_html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the ID of the search input so we can bind to it
content = content.replace(
    'placeholder="Search by Address, Txn Hash, Entity, ENS, Domain..."',
    'id="main-search-input" placeholder="Enter Seed Address and press Enter to trace..."'
)

# Update the right sidebar IDs for dynamic injection
content = content.replace('Ethereum Address</span><span class="text-xs font-medium text-slate-800">', 'Ethereum Address</span><span id="sidebar-chain" class="text-xs font-medium text-slate-800">')
content = content.replace('Lionsgate Cluster 6987', '<span id="sidebar-entity">Lionsgate Cluster</span>')


new_script = """
    <script>
        let Graph = null;
        
        // Setup Image Caching for crisp canvas rendering
        const imageCache = {};
        function getCachedImage(url) {
            if (!url) return null;
            if (imageCache[url]) return imageCache[url];
            const img = new Image();
            img.src = url;
            img.crossOrigin = "Anonymous";
            imageCache[url] = img;
            return img;
        }

        // Preload Binance Logo
        getCachedImage('https://cryptologos.cc/logos/bnb-bnb-logo.png');

        // NEMESIS TRACING ENGINE INTEGRATION
        let ws = null;
        let wsReconnectDelay = 1000;
        let traceNodesMap = new Map();
        let traceEdgesMap = new Map();
        const graphData = { nodes: [], links: [] };

        function initGraph() {
            const container = document.getElementById('graph-container');
            
            Graph = ForceGraph()(container)
                .graphData(graphData)
                .backgroundColor('#f8fafc')
                .cooldownTicks(100)
                .nodeId('id')
                .nodeCanvasObject((node, ctx, globalScale) => {
                    const R = 22;
                    ctx.shadowColor = 'rgba(0,0,0,0.08)';
                    ctx.shadowBlur = 15;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, R, 0, 2 * Math.PI, false);
                    ctx.fillStyle = '#ffffff';
                    ctx.fill();
                    ctx.shadowColor = 'transparent';
                    ctx.lineWidth = 1 / globalScale;
                    ctx.strokeStyle = '#e2e8f0';
                    ctx.stroke();

                    let isCEX = (node.typeStr || "").toLowerCase().includes("cex") || (node.nameStr || "").toLowerCase().includes("exchange") || (node.nameStr || "").toLowerCase().includes("binance");
                    if (isCEX) {
                        const img = getCachedImage('https://cryptologos.cc/logos/bnb-bnb-logo.png');
                        if (img && img.complete) {
                            ctx.save();
                            ctx.beginPath();
                            ctx.arc(node.x, node.y, R - 2, 0, 2 * Math.PI);
                            ctx.clip();
                            ctx.drawImage(img, node.x - R + 4, node.y - R + 4, (R - 4) * 2, (R - 4) * 2);
                            ctx.restore();
                        }
                    } else {
                        ctx.font = `900 ${R * 1.1}px "Font Awesome 6 Free"`;
                        ctx.fillStyle = '#3b82f6';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText('\\uf555', node.x, node.y);
                    }

                    const badgeR = R * 0.35;
                    const badgeX = node.x + R * 0.7;
                    const badgeY = node.y + R * 0.7;
                    ctx.beginPath();
                    ctx.arc(badgeX, badgeY, badgeR, 0, 2 * Math.PI);
                    ctx.fillStyle = node.badgeColor || '#3b82f6';
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 2 / globalScale;
                    ctx.stroke();
                    
                    ctx.font = `900 ${badgeR * 1.1}px "Font Awesome 6 Free"`;
                    ctx.fillStyle = '#ffffff';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(node.badgeIcon || '\\uf00c', badgeX, badgeY);

                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'top';
                    ctx.font = `bold ${5}px Inter`;
                    ctx.fillStyle = '#2563eb';
                    ctx.fillText(node.valStr || '$0.00', node.x, node.y + R + 6);
                    ctx.font = `bold ${4}px Inter`;
                    ctx.fillStyle = isCEX ? '#2563eb' : '#3b82f6';
                    ctx.fillText(node.nameStr || 'Unknown', node.x, node.y + R + 13);
                    ctx.font = `600 ${3.5}px Inter`;
                    ctx.fillStyle = '#64748b';
                    ctx.fillText(node.typeStr || 'EOA', node.x, node.y + R + 18);
                })
                .nodePointerAreaPaint((node, color, ctx) => {
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 25, 0, 2 * Math.PI);
                    ctx.fill();
                })
                .linkCanvasObjectMode(() => 'after')
                .linkCanvasObject((link, ctx) => {
                    const start = link.source;
                    const end = link.target;
                    if (typeof start !== 'object' || typeof end !== 'object') return;
                    const midX = start.x + (end.x - start.x) / 2;
                    const midY = start.y + (end.y - start.y) / 2;
                    ctx.save();
                    ctx.translate(midX, midY);
                    let angle = Math.atan2(end.y - start.y, end.x - start.x);
                    if (angle > Math.PI / 2 || angle < -Math.PI / 2) angle += Math.PI;
                    ctx.rotate(angle);
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = `bold ${3.5}px Inter`;
                    ctx.fillStyle = '#ef4444';
                    ctx.fillText(`↓ OUTFLOW`, 0, -8);
                    ctx.font = `bold ${4.5}px Inter`;
                    ctx.fillText(link.valStr || '$0.00', 0, -3.5);
                    ctx.font = `400 ${3.5}px Inter`;
                    ctx.fillStyle = '#64748b';
                    ctx.fillText(link.hashStr || '0x...', 0, 3.5);
                    if(link.tagStr) {
                        ctx.font = `bold ${3}px Inter`;
                        const tw = ctx.measureText(link.tagStr).width;
                        ctx.fillStyle = '#f1f5f9';
                        ctx.beginPath();
                        ctx.roundRect(-tw/2 - 2, 6.5, tw + 4, 5, 1.5);
                        ctx.fill();
                        ctx.strokeStyle = '#e2e8f0';
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                        ctx.fillStyle = '#64748b';
                        ctx.fillText(link.tagStr, 0, 9);
                    }
                    ctx.restore();
                })
                .linkColor(() => '#3b82f6')
                .linkWidth(1)
                .linkDirectionalArrowLength(4.5)
                .linkDirectionalArrowRelPos(1)
                .linkDirectionalArrowColor(() => '#3b82f6')
                .onNodeClick(node => {
                    let idEl = document.getElementById('sidebar-id');
                    let typeEl = document.getElementById('sidebar-type');
                    let usdEl = document.getElementById('sidebar-usd');
                    let chainEl = document.getElementById('sidebar-chain');
                    let entityEl = document.getElementById('sidebar-entity');
                    if(idEl) idEl.innerText = node.displayId || node.id;
                    if(typeEl) typeEl.innerText = (node.typeStr || "").toUpperCase().includes("CEX") ? 'CEX' : 'EOA';
                    if(usdEl) usdEl.innerText = node.valStr || "$0.00";
                    if(chainEl) chainEl.innerText = node.chain || "UNKNOWN";
                    if(entityEl) entityEl.innerText = node.nameStr || "PRIVATE WALLET";
                });
                
            setTimeout(() => { Graph.zoomToFit(400, 50); }, 300);
        }

        function handleNewNode(d) {
            let added = false;
            if (!traceNodesMap.has(d.from)) {
                let isCEX = (d.sender_entity || "").toUpperCase().includes("EXCHANGE");
                let n = { 
                    id: d.from, 
                    displayId: d.from.substring(0, 10) + '...',
                    nameStr: (d.sender_entity || 'Unknown Wallet').toUpperCase(), 
                    typeStr: isCEX ? 'CEX' : 'EOA', 
                    valStr: `$${(d.usd || d.amount).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`,
                    badgeColor: isCEX ? '#eab308' : '#3b82f6',
                    badgeIcon: isCEX ? '\\uf19c' : '\\uf555',
                    chain: d.chain,
                    totalOutflow: d.usd || d.amount
                };
                traceNodesMap.set(d.from, n);
                graphData.nodes.push(n);
                added = true;
            } else {
                let n = traceNodesMap.get(d.from);
                n.totalOutflow = (n.totalOutflow || 0) + (d.usd || d.amount);
                n.valStr = `$${n.totalOutflow.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                added = true;
            }

            if (!traceNodesMap.has(d.to)) {
                let isCEX = (d.receiver_entity || "").toUpperCase().includes("EXCHANGE") || d.is_terminal;
                let n = { 
                    id: d.to, 
                    displayId: d.to.substring(0, 10) + '...',
                    nameStr: (d.receiver_entity || 'Unknown Wallet').toUpperCase(), 
                    typeStr: isCEX ? 'CEX / TERMINAL' : 'EOA', 
                    valStr: '$0.00',
                    badgeColor: isCEX ? '#eab308' : '#3b82f6',
                    badgeIcon: isCEX ? '\\uf19c' : '\\uf555',
                    chain: d.chain,
                    totalOutflow: 0
                };
                traceNodesMap.set(d.to, n);
                graphData.nodes.push(n);
                added = true;
            }

            let edgeId = d.from + "-" + d.to + "-" + d.tx;
            if (!traceEdgesMap.has(edgeId)) {
                let e = { 
                    id: edgeId, 
                    source: d.from, 
                    target: d.to, 
                    valStr: `$${(d.usd || d.amount).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`, 
                    hashStr: d.tx.substring(0, 8) + '...', 
                    tagStr: d.chain 
                };
                traceEdgesMap.set(edgeId, e);
                graphData.links.push(e);
                added = true;
            }
            
            if (added && Graph) {
                // Update graph
                Graph.graphData({ nodes: [...graphData.nodes], links: [...graphData.links] });
            }
        }

        function connectWebSocket(traceId) {
            if (!traceId) return;
            let protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
            let host = window.location.host;
            let wsUrl = protocol + host + "/ws/" + traceId;
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                wsReconnectDelay = 1000;
                console.log("[WS] Connected to OmniChain Engine");
            };

            ws.onmessage = (msg) => {
                let d = JSON.parse(msg.data);
                if(d.type === "INIT") {
                    traceNodesMap.clear(); traceEdgesMap.clear();
                    graphData.nodes = []; graphData.links = [];
                    if(Graph) Graph.graphData(graphData);
                    console.log("Trace INIT");
                }
                else if(d.type === "LEDGER") {
                    handleNewNode(d);
                }
                else if(d.type === "PROGRESS") {
                    console.log("Trace Progress:", d.percentage);
                }
                else if(d.type === "COMPLETE") {
                    console.log("Trace Complete");
                }
            };
            
            ws.onclose = () => {
                console.warn("[WS] Disconnected.");
                setTimeout(() => connectWebSocket(traceId), wsReconnectDelay);
                wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
            };
        }

        async function submitTrace() {
            let searchInput = document.getElementById("main-search-input");
            let seeds = searchInput ? searchInput.value.trim() : "";
            if (!seeds) return;
            
            console.log("Starting trace for:", seeds);
            
            const backendUrl = '';
            try {
                const response = await fetch(`${backendUrl}/api/start_trace`, {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        seeds: seeds, 
                        target_amount: "", 
                        target_currency: "USD",
                        start_date: "",
                        end_date: "",
                        chain_override: "AUTO",
                        max_depth: 12,
                        max_hops: 1000
                    })
                });
                const data = await response.json();
                if (data.trace_id) {
                    connectWebSocket(data.trace_id);
                }
            } catch(e) { console.error("Trace Error", e); }
        }

        window.addEventListener('DOMContentLoaded', () => {
            initGraph();
            
            let searchInput = document.getElementById("main-search-input");
            if (searchInput) {
                searchInput.addEventListener('keypress', function (e) {
                    if (e.key === 'Enter') {
                        submitTrace();
                    }
                });
            }
            
            window.addEventListener('resize', () => {
                const container = document.getElementById('graph-container');
                if (Graph && container) {
                    Graph.width(container.clientWidth).height(container.clientHeight);
                }
            });
        });

        // Widget Toggle Logic
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.toggle-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const container = this.closest('.widget-container');
                    const content = container.querySelector('.widget-content');
                    const icon = this.querySelector('i');
                    if (content.classList.contains('hidden')) {
                        content.classList.remove('hidden');
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    } else {
                        content.classList.add('hidden');
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    }
                    if (Graph && !content.classList.contains('hidden')) {
                        setTimeout(() => {
                            const graphContainer = document.getElementById('graph-container');
                            if (graphContainer) {
                                Graph.width(graphContainer.clientWidth).height(graphContainer.clientHeight);
                            }
                        }, 50);
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

# Replace the original script tag and everything after it with our new logic
modified_content = re.sub(r'<script>\s*let Graph = null;.*', new_script, content, flags=re.DOTALL)

with open(target_html_path, "w", encoding="utf-8") as f:
    f.write(modified_content)

print(f"Successfully migrated template to {target_html_path}")
