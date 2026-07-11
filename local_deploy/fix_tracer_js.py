import os

html_path = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates\nemesis_tracer.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add updateMetricsUI function
if "function updateMetricsUI()" not in content:
    metrics_func = """
        function updateMetricsUI() {
            document.getElementById('metric-addresses').textContent = metrics.totalAddresses.toLocaleString();
            document.getElementById('metric-tx').textContent = metrics.totalTransactions.toLocaleString();
            document.getElementById('metric-volume').textContent = "$" + metrics.totalVolumeUsd.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('metric-alerts').textContent = metrics.highRiskAlerts.toLocaleString();
        }
"""
    content = content.replace("function copySidebarId() {", metrics_func + "\n        function copySidebarId() {")

# 2. Add 5 layouts UI
layout_ui = """
                            <select id="graph-layout-select" onchange="changeGraphLayout(this.value)" class="px-3 py-1 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50 focus:outline-none focus:ring-1 focus:ring-blue-500">
                                <option value="force">Force Directed</option>
                                <option value="circular">Circular Layout</option>
                                <option value="dagre">Hierarchical (Tree)</option>
                                <option value="radial">Radial Layout</option>
                                <option value="grid">Grid Layout</option>
                            </select>
                            <button onclick="togglePhysics()" class="px-3 py-1 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50"><i class="fa-solid fa-magnet mr-1"></i> Toggle Physics</button>
"""
content = content.replace('<button onclick="togglePhysics()" class="px-3 py-1 bg-white border border-slate-200 rounded text-xs font-semibold text-slate-600 hover:bg-slate-50"><i class="fa-solid fa-magnet mr-1"></i> Toggle Physics</button>', layout_ui)

# 3. Add Layout Logic (using d3-force positioning modifications or basic geometric calculations for the layouts, as forceGraph2D allows custom node coordinates)
layout_logic = """
        function changeGraphLayout(layoutType) {
            let nodes = window.graphData.nodes;
            let width = document.getElementById('graph-container').clientWidth;
            let height = document.getElementById('graph-container').clientHeight;
            let cx = 0, cy = 0;
            
            if(layoutType === 'force') {
                physicsEnabled = true;
                Graph.d3Force('charge').strength(-400);
                Graph.d3ReheatSimulation();
            } else {
                physicsEnabled = false;
                Graph.d3Force('charge').strength(0);
                
                if(layoutType === 'circular') {
                    let r = Math.min(width, height) / 2 * 0.8;
                    let angleStep = (2 * Math.PI) / nodes.length;
                    nodes.forEach((n, i) => {
                        n.fx = cx + r * Math.cos(i * angleStep);
                        n.fy = cy + r * Math.sin(i * angleStep);
                    });
                } else if(layoutType === 'grid') {
                    let cols = Math.ceil(Math.sqrt(nodes.length));
                    let spacing = 150;
                    let startX = cx - ((cols-1)*spacing)/2;
                    let startY = cy - ((cols-1)*spacing)/2;
                    nodes.forEach((n, i) => {
                        n.fx = startX + (i % cols) * spacing;
                        n.fy = startY + Math.floor(i / cols) * spacing;
                    });
                } else if(layoutType === 'radial') {
                    let rStep = 100;
                    nodes.forEach((n, i) => {
                        if(i===0){ n.fx = cx; n.fy = cy; }
                        else {
                            let ring = Math.ceil(Math.sqrt(i));
                            let r = ring * rStep;
                            let maxInRing = (ring*ring) - ((ring-1)*(ring-1));
                            let idxInRing = i - ((ring-1)*(ring-1));
                            let angle = (2 * Math.PI / maxInRing) * idxInRing;
                            n.fx = cx + r * Math.cos(angle);
                            n.fy = cy + r * Math.sin(angle);
                        }
                    });
                } else if(layoutType === 'dagre') {
                    // Simple top-down tree based on BFS depth logic
                    let levels = {};
                    let currentLevel = [nodes[0]];
                    let visited = new Set();
                    if(nodes[0]) visited.add(nodes[0].id);
                    let depth = 0;
                    while(currentLevel.length > 0) {
                        levels[depth] = currentLevel;
                        let nextLevel = [];
                        currentLevel.forEach(node => {
                            let outgoing = window.graphData.links.filter(l => (l.source.id || l.source) === node.id);
                            outgoing.forEach(link => {
                                let targetId = link.target.id || link.target;
                                if(!visited.has(targetId)) {
                                    visited.add(targetId);
                                    let targetNode = nodes.find(n => n.id === targetId);
                                    if(targetNode) nextLevel.push(targetNode);
                                }
                            });
                        });
                        currentLevel = nextLevel;
                        depth++;
                    }
                    
                    let ySpacing = 150;
                    let startY = cy - ((depth-1)*ySpacing)/2;
                    Object.keys(levels).forEach(d => {
                        let row = levels[d];
                        let xSpacing = 150;
                        let startX = cx - ((row.length-1)*xSpacing)/2;
                        row.forEach((n, i) => {
                            n.fx = startX + i * xSpacing;
                            n.fy = startY + d * ySpacing;
                        });
                    });
                }
                
                Graph.d3ReheatSimulation();
            }
        }
"""

if "function changeGraphLayout" not in content:
    content = content.replace("function togglePhysics() {", layout_logic + "\n        function togglePhysics() {")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)
print("SUCCESS: Injected updateMetricsUI and layout options into nemesis_tracer.html")
