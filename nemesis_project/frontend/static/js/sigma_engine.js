/**
 * NEMESIS TRACER v6
 * Graph Engine (Sigma.js + Graphology + Layer 2 Overlays)
 */

class NemesisGraphEngine {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) throw new Error("Graph container not found.");

        // Layer 1: Sigma Canvas
        this.sigmaContainer = document.createElement("div");
        this.sigmaContainer.style.width = "100%";
        this.sigmaContainer.style.height = "100%";
        this.sigmaContainer.style.position = "absolute";
        this.sigmaContainer.style.top = "0";
        this.sigmaContainer.style.left = "0";
        this.container.appendChild(this.sigmaContainer);

        // Layer 2: HTML Overlay Container
        this.overlayContainer = document.createElement("div");
        this.overlayContainer.style.position = "absolute";
        this.overlayContainer.style.top = "0";
        this.overlayContainer.style.left = "0";
        this.overlayContainer.style.width = "100%";
        this.overlayContainer.style.height = "100%";
        this.overlayContainer.style.pointerEvents = "none"; // Let clicks pass through to Sigma
        this.overlayContainer.style.zIndex = "10";
        this.container.appendChild(this.overlayContainer);

        // Graphology Instance
        this.graph = new graphology.Graph();

        // Sigma Instance
        this.renderer = new sigma.Sigma(this.graph, this.sigmaContainer, {
            renderEdgeLabels: true,
            defaultNodeColor: "#0f172a",
            defaultEdgeColor: "#94a3b8",
            defaultEdgeType: "arrow",
        });
        
        this.nodeOverlays = {};
        
        // Bind Camera updates to DOM Sync
        this.renderer.getCamera().on("updated", () => this._syncOverlays());
        
        this._bindEvents();
    }

    _bindEvents() {
        this.renderer.on("enterNode", (e) => {
            this.container.style.cursor = "pointer";
            // Render hover pulse effect here
        });
        
        this.renderer.on("leaveNode", () => {
            this.container.style.cursor = "default";
        });
        
        this.renderer.on("clickNode", (e) => {
            console.log("Selected Node:", e.node);
            // Handle Side Panel opening
        });
    }

    addNode(id, data) {
        // Fallback layout if none provided
        if (data.x === undefined) data.x = Math.random() * 10;
        if (data.y === undefined) data.y = Math.random() * 10;
        if (data.size === undefined) data.size = 15;
        
        this.graph.addNode(id, data);
        this._createNodeOverlay(id, data);
    }

    addEdge(source, target, data) {
        const edgeId = this.graph.addEdge(source, target, data);
        this._createEdgeOverlay(edgeId, source, target, data);
        return edgeId;
    }

    _createEdgeOverlay(edgeId, source, target, data) {
        const el = document.createElement("div");
        el.className = "edge-overlay absolute flex flex-col items-center pointer-events-none transition-transform bg-white/90 backdrop-blur-sm rounded-lg p-1.5 border border-slate-200 shadow-sm z-0";
        el.style.transform = "translate(-50%, -50%)"; // Center over midpoint
        
        // Transaction Badge Layout
        el.innerHTML = `
            <div class="flex items-center gap-1 font-bold text-[10px] text-slate-800">
                <span class="text-emerald-500">🟢</span> ${data.token || "USDT"}
            </div>
            <div class="text-[9px] font-extrabold text-red-500 tracking-wider">OUTFLOW</div>
            <div class="font-mono font-bold text-slate-900 text-[11px]">⬇ ${data.amount || "$0.00"}</div>
            <div class="text-[9px] font-bold text-slate-400 bg-slate-100 px-1 rounded">${data.chain || "TRC20"}</div>
        `;
        
        this.overlayContainer.appendChild(el);
        
        if (!this.edgeOverlays) this.edgeOverlays = {};
        this.edgeOverlays[edgeId] = { element: el, source, target };
    }

    _createNodeOverlay(id, data) {
        const el = document.createElement("div");
        el.className = "node-overlay bg-white rounded-xl shadow-xl border-2 flex flex-col items-center justify-center pointer-events-auto transition-transform cursor-pointer";
        el.style.position = "absolute";
        el.style.transform = "translate(-50%, -50%)"; // Center over coordinate
        el.style.minWidth = "180px";
        el.style.padding = "12px";
        
        // Border styling based on category
        if (data.category === "Exchange") el.classList.add("border-blue-500", "shadow-blue-500/20");
        else if (data.category === "Sanctioned") el.classList.add("border-red-500", "shadow-red-500/20");
        else if (data.category === "Mixer") el.classList.add("border-purple-500", "shadow-purple-500/20");
        else el.classList.add("border-slate-200");
        
        // 1. Verified Badge (Top Right Absolute)
        if (data.verified) {
            const badge = document.createElement("div");
            badge.className = "absolute -top-3 -right-3 bg-emerald-100 text-emerald-700 text-[10px] font-bold px-2 py-1 rounded-full border border-emerald-200 shadow-sm flex items-center gap-1";
            badge.innerHTML = `<i class="fa-solid fa-check-circle"></i> VERIFIED`;
            el.appendChild(badge);
        }

        // 2. Official Logo
        const iconContainer = document.createElement("div");
        iconContainer.className = "w-12 h-12 rounded-lg mb-2 flex items-center justify-center bg-slate-50 border border-slate-100";
        if (data.logo_url) {
            iconContainer.innerHTML = `<img src="${data.logo_url}" class="w-8 h-8 object-contain">`;
        } else {
            iconContainer.innerHTML = `<i class="fa-solid fa-wallet text-slate-400 text-xl"></i>`;
        }
        el.appendChild(iconContainer);
        
        // 3. Balance
        const balance = document.createElement("div");
        balance.className = "font-mono font-bold text-slate-900 text-sm mb-1";
        balance.innerText = data.balance || "$0.00";
        el.appendChild(balance);
        
        // 4. Entity Name
        const name = document.createElement("div");
        name.className = "font-extrabold text-slate-800 text-[11px] tracking-wider uppercase";
        name.innerText = data.label || "UNKNOWN ENTITY";
        el.appendChild(name);
        
        // 5. Category
        const category = document.createElement("div");
        category.className = "text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-2";
        category.innerText = data.category || "PRIVATE WALLET";
        el.appendChild(category);
        
        // 6. Address
        const address = document.createElement("div");
        address.className = "font-mono text-slate-600 text-[10px] bg-slate-100 px-2 py-1 rounded w-full text-center truncate border border-slate-200";
        address.innerText = id.substring(0, 8) + "..." + id.substring(id.length - 4);
        el.appendChild(address);
        
        // 7. Footer (Chain)
        const footer = document.createElement("div");
        footer.className = "text-[9px] text-slate-400 mt-2 flex items-center gap-1";
        footer.innerHTML = `<span class="font-bold">${data.chain || "TRON"}</span> • ${data.wallet_type || "External"}`;
        el.appendChild(footer);
        
        // Click handler
        el.addEventListener("click", () => {
            console.log("Clicked Overlay:", id);
            // Highlight node or open drawer
        });

        this.overlayContainer.appendChild(el);
        this.nodeOverlays[id] = { element: el };
    }

    _syncOverlays() {
        const camera = this.renderer.getCamera();
        const ratio = camera.ratio;
        const zoomLevel = 1 / ratio; // Higher ratio = zoomed out

        for (const nodeId in this.nodeOverlays) {
            const overlay = this.nodeOverlays[nodeId];
            
            // Get screen coordinates of the node from Sigma
            const nodeCoords = this.renderer.getNodeDisplayData(nodeId);
            if (!nodeCoords) continue;
            
            // Semantic Zooming Logic
            if (zoomLevel < 0.4) {
                // Fully zoomed out: Hide overlay completely, let WebGL dot render
                overlay.element.style.display = "none";
                continue;
            } else if (zoomLevel < 0.8) {
                // Medium zoom: Show small version (just logo and name)
                overlay.element.style.display = "flex";
                overlay.element.style.transform = `translate(-50%, -50%) scale(${zoomLevel * 0.5})`;
                // Hide details
                Array.from(overlay.element.children).forEach((child, idx) => {
                    if (idx > 1) child.style.display = "none"; // Hide everything after Logo
                });
            } else {
                // Zoomed in: Show full Enterprise Card
                overlay.element.style.display = "flex";
                overlay.element.style.transform = `translate(-50%, -50%) scale(${Math.min(zoomLevel * 0.8, 1.2)})`;
                Array.from(overlay.element.children).forEach((child) => {
                    child.style.display = "block";
                });
            }

            // Position absolute DOM element over WebGL coordinate
            overlay.element.style.left = `${nodeCoords.x}px`;
            overlay.element.style.top = `${nodeCoords.y}px`;
            
            // Optional: Hide WebGL node when overlay is active so they don't overlap poorly
            // this.graph.setNodeAttribute(nodeId, "hidden", true);
        }

        // Sync Edge Overlays (Transaction Badges)
        if (this.edgeOverlays) {
            for (const edgeId in this.edgeOverlays) {
                const overlay = this.edgeOverlays[edgeId];
                
                if (zoomLevel < 0.6) {
                    overlay.element.style.display = "none";
                    continue;
                }
                
                const sourceCoords = this.renderer.getNodeDisplayData(overlay.source);
                const targetCoords = this.renderer.getNodeDisplayData(overlay.target);
                
                if (!sourceCoords || !targetCoords) continue;
                
                // Calculate Midpoint
                const midX = (sourceCoords.x + targetCoords.x) / 2;
                const midY = (sourceCoords.y + targetCoords.y) / 2;
                
                overlay.element.style.display = "flex";
                overlay.element.style.left = `${midX}px`;
                overlay.element.style.top = `${midY}px`;
                overlay.element.style.transform = `translate(-50%, -50%) scale(${Math.min(zoomLevel * 0.7, 1.0)})`;
            }
        }
    }
}

// Export for global use in nemesis_tracer.html
window.NemesisGraphEngine = NemesisGraphEngine;
