// Ledger Minimize Toggle
let isLedgerMinimized = false;
function toggleLedger() {
    const panel = document.getElementById('ledger-panel');
    const icon = document.getElementById('ledger-toggle-icon');
    
    if (isLedgerMinimized) {
        panel.classList.remove('ledger-minimized');
        icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
    } else {
        panel.classList.add('ledger-minimized');
        icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
    }
    isLedgerMinimized = !isLedgerMinimized;
    
    // Re-fit graph after transition
    setTimeout(() => {
        if(window.Graph) {
            const container = document.getElementById('graph-container');
            window.Graph.width(container.clientWidth).height(container.clientHeight);
        }
    }, 350);
}

// Preload images
const imgs = {
    binance: new Image(),
    usdt: new Image(),
    wallet: new Image(),
    unknown: new Image()
};
imgs.binance.src = 'https://cryptologos.cc/logos/bnb-bnb-logo.png';
imgs.usdt.src = 'https://cryptologos.cc/logos/tether-usdt-logo.png';
imgs.wallet.src = 'https://cdn-icons-png.flaticon.com/512/855/855279.png'; // Mock wallet icon
imgs.unknown.src = 'https://cdn-icons-png.flaticon.com/512/855/855279.png'; 

let graphData = { nodes: [], links: [] };

async function runTrace() {
    // Read from sessionStorage
    const sessionDataRaw = sessionStorage.getItem('nemesis_trace_init');
    if (!sessionDataRaw) {
        // If accessed without going through landing, redirect to landing
        window.location.href = '/tracer_landing.html';
        return;
    }

    const tracePayload = JSON.parse(sessionDataRaw);
    let targetAddress = tracePayload.targets || "";
    let lossAmount = tracePayload.loss || "0";
    
    if (!targetAddress) return;

    document.getElementById('loading-overlay').classList.remove('hidden');
    document.getElementById('loading-overlay').classList.add('flex');

    try {
        const formData = new FormData();
        formData.append('target_address', targetAddress);
        formData.append('loss_amount', lossAmount);
        // Can append networks and date if backend supports it
        // formData.append('networks', JSON.stringify(tracePayload.networks));
        
        const response = await fetch('/trace', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error("API Error");
        const data = await response.json();
        
        // Convert app.py node format to ForceGraph format
        const fNodes = data.nodes.map((n, idx) => {
            const isExchange = n.type === 'exchange' || n.group === 1 || n.group === 7 || (n.label && n.label.toLowerCase().includes('exchange'));
            const isSeed = n.group === 6;
            const type = isExchange ? 'EXCHANGE' : (isSeed ? 'ORIGIN SEED' : 'UNKNOWN ENTITY');
            const name = isExchange ? "BINANCE" : (isSeed ? "SUBJECT" : "WALLET");
            
            const val = n.total_in ? `$${parseFloat(n.total_in).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : (lossAmount || "$0.00");
            
            return {
                id: n.id,
                name: name,
                type: type,
                val: val,
                icon: isExchange ? imgs.binance : imgs.wallet,
                isCEX: isExchange,
                badge: isExchange ? 'check' : 'question'
            };
        });

        // Convert app.py edge format to ForceGraph links
        const fLinks = data.edges.map(e => {
            const amountStr = e.amount_usd ? `$${parseFloat(e.amount_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : (e.amount ? `$${e.amount}` : '$0.00');
            const hashShort = e.tx_hash ? e.tx_hash.substring(0,6) + '...' + e.tx_hash.substring(e.tx_hash.length-4) : 'Unknown';
            const token = e.token_symbol || 'USDT';
            const network = token === 'USDT' ? 'TRC20' : 'ERC20';

            return {
                source: e.from_address,
                target: e.to_address,
                label: `${token} (${network})`,
                amount: amountStr,
                hash: hashShort,
                tag: network
            };
        });

        graphData = { nodes: fNodes, links: fLinks };
        window.Graph.graphData(graphData);
        
        setTimeout(() => { window.Graph.zoomToFit(400, 50); }, 500);
        
        // Update stats
        document.querySelectorAll('.stat-card .text-lg')[0].innerHTML = `${fNodes.length} <span class="text-[10px] text-emerald-500">+</span>`;
        document.querySelectorAll('.stat-card .text-lg')[1].innerHTML = `${fLinks.length} <span class="text-[10px] text-emerald-500">+</span>`;
        
        let vol = 0;
        data.edges.forEach(e => { if(e.amount_usd) vol += parseFloat(e.amount_usd); });
        document.querySelectorAll('.stat-card .text-lg')[2].innerHTML = `$${vol.toLocaleString(undefined, {minimumFractionDigits:2})} <span class="text-[10px] text-emerald-500">+</span>`;

        renderLedger(data.edges);

    } catch (err) {
        console.error(err);
        alert("Failed to run trace: " + err);
    } finally {
        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('loading-overlay').classList.remove('flex');
    }
}

function renderLedger(edges) {
    const tbody = document.querySelector('tbody');
    tbody.innerHTML = '';
    document.getElementById('ledger-count').innerText = `${edges.length} Records`;
    
    edges.forEach(edge => {
        const amtUsdStr = edge.amount_usd ? `$${parseFloat(edge.amount_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : '-';
        
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition cursor-pointer";
        tr.innerHTML = `
            <td class="px-4 py-2">${edge.timestamp || 'Unknown'}</td>
            <td class="px-4 py-2"><span class="bg-blue-50 text-blue-600 border border-blue-100 px-1.5 py-0.5 rounded text-[9px] uppercase font-bold">Transfer</span></td>
            <td class="px-4 py-2 text-blue-600 hover:underline">${edge.tx_hash ? edge.tx_hash.substring(0,10)+'...' : 'N/A'}</td>
            <td class="px-4 py-2">${edge.from_address ? edge.from_address.substring(0,12)+'...' : 'Unknown'}</td>
            <td class="px-4 py-2">${edge.to_address ? edge.to_address.substring(0,12)+'...' : 'Unknown'}</td>
            <td class="px-4 py-2 font-semibold">Unknown Entity</td>
            <td class="px-4 py-2 text-right font-black text-slate-800">${amtUsdStr}</td>
            <td class="px-4 py-2">${edge.token_symbol || 'ETH'} Transfer</td>
            <td class="px-4 py-2 text-slate-500 font-sans">Hop</td>
            <td class="px-4 py-2 text-purple-600">${edge.to_address ? edge.to_address.substring(0,6)+'...' : ''}</td>
            <td class="px-4 py-2"><span class="text-emerald-600 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-bold text-[9px]">99%</span></td>
            <td class="px-4 py-2 text-slate-500 font-sans">Automated Trace</td>
            <td class="px-4 py-2 text-slate-500 font-sans">Traced via engine</td>
        `;
        tbody.appendChild(tr);
    });
}

function resolveAssets() {
    console.log("Resolving assets...");
}

// Initialize ForceGraph with the exact "Modern Card Style" specs from the user's Design Concepts
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('graph-container');

    window.Graph = ForceGraph()(container)
        .graphData(graphData)
        .backgroundColor('transparent')
        .cooldownTicks(0) // Static linear
        .enableZoomPanInteraction(true)
        .nodeCanvasObject((node, ctx, globalScale) => {
            const w = 120;
            const h = 140;
            
            // Draw "Modern Card Style" (Design 1) background
            ctx.fillStyle = '#ffffff';
            ctx.shadowColor = 'rgba(0,0,0,0.05)';
            ctx.shadowBlur = 10;
            ctx.beginPath(); ctx.roundRect(node.x - w/2, node.y - h/2, w, h, 8); ctx.fill();
            
            ctx.shadowColor = 'transparent';
            ctx.lineWidth = 1/globalScale;
            ctx.strokeStyle = '#e2e8f0';
            ctx.stroke();

            // Icon Circle
            const r = 24;
            ctx.beginPath(); ctx.arc(node.x, node.y - 20, r, 0, 2*Math.PI);
            ctx.fillStyle = node.isCEX ? '#f8fafc' : '#eff6ff';
            ctx.fill();
            ctx.strokeStyle = node.isCEX ? '#e2e8f0' : '#bfdbfe';
            ctx.stroke();

            // Draw Image
            if (node.icon.complete) {
                ctx.drawImage(node.icon, node.x - 16, node.y - 36, 32, 32);
            }

            // Badges
            if (node.badge === 'check') {
                ctx.beginPath(); ctx.arc(node.x + 16, node.y - 4, 8, 0, 2*Math.PI);
                ctx.fillStyle = '#10b981'; ctx.fill();
                ctx.font = '900 8px "Font Awesome 6 Free"'; ctx.fillStyle = '#fff';
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('\uf00c', node.x + 16, node.y - 4);
            } else if (node.badge === 'question') {
                ctx.beginPath(); ctx.arc(node.x + 16, node.y - 4, 8, 0, 2*Math.PI);
                ctx.fillStyle = '#64748b'; ctx.fill();
                ctx.font = '900 8px "Font Awesome 6 Free"'; ctx.fillStyle = '#fff';
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('\uf128', node.x + 16, node.y - 4);
            }

            // Typography
            ctx.textAlign = 'center';
            
            ctx.font = 'bold 12px Inter';
            ctx.fillStyle = node.isCEX ? '#2563eb' : '#2563eb';
            ctx.fillText(node.val, node.x, node.y + 20);

            // Pill
            ctx.font = 'bold 8px Inter';
            const textWidth = ctx.measureText(node.name).width;
            ctx.fillStyle = '#eff6ff';
            ctx.beginPath(); ctx.roundRect(node.x - textWidth/2 - 4, node.y + 30, textWidth + 8, 14, 4); ctx.fill();
            ctx.fillStyle = '#2563eb';
            ctx.fillText(node.name, node.x, node.y + 40);

            ctx.font = '600 8px Inter';
            ctx.fillStyle = '#64748b';
            ctx.fillText(node.type, node.x, node.y + 55);
        })
        .linkCanvasObjectMode(() => 'after')
        .linkCanvasObject((link, ctx) => {
            const start = link.source; const end = link.target;
            const midX = start.x + (end.x - start.x) / 2;
            const midY = start.y + (end.y - start.y) / 2;

            ctx.save(); ctx.translate(midX, midY - 15);
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';

            // Label Top (e.g. USDT TRC20)
            ctx.font = 'bold 9px Inter';
            ctx.fillStyle = '#475569';
            ctx.fillText(link.label, 0, -15);
            
            // Outflow & Amount
            ctx.font = 'bold 8px Inter';
            ctx.fillStyle = '#64748b';
            ctx.fillText('OUTFLOW', 0, -3);
            ctx.font = 'bold 11px Inter';
            ctx.fillStyle = '#ef4444';
            ctx.fillText('↓ ' + link.amount, 0, 8);

            // Hash
            ctx.font = '10px JetBrains Mono';
            ctx.fillStyle = '#64748b';
            ctx.fillText(link.hash, 0, 30);
            
            // Tag bottom
            ctx.font = 'bold 8px Inter';
            ctx.fillStyle = '#e0e7ff';
            const tw = ctx.measureText(link.tag).width;
            ctx.beginPath(); ctx.roundRect(-tw/2 - 4, 38, tw + 8, 12, 2); ctx.fill();
            ctx.fillStyle = '#4338ca';
            ctx.fillText(link.tag, 0, 44);

            ctx.restore();
        })
        .linkColor(() => '#2563eb')
        .linkWidth(2)
        .linkDirectionalArrowLength(6)
        .linkDirectionalArrowRelPos(1);

    // Initial zoom
    setTimeout(() => { Graph.zoomToFit(200, 50); }, 200);

    // Handle window resize
    window.addEventListener('resize', () => {
        Graph.width(container.clientWidth).height(container.clientHeight);
    });

    // Check if we have trace payload in session, and if so, run it automatically.
    const sessionDataRaw = sessionStorage.getItem('nemesis_trace_init');
    if(sessionDataRaw) {
        runTrace();
    } else {
        window.location.href = '/tracer_landing.html';
    }
});
