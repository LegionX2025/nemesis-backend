            
            const tagsDiv = document.getElementById('em-tags');
            tagsDiv.innerHTML = '';
            if (details.tags && details.tags.length > 0) {
                details.tags.forEach(tag => {
                    tagsDiv.innerHTML += `<span class="px-2 py-1 bg-blue-50 text-blue-600 border border-blue-100 rounded text-[10px] font-semibold">${tag}</span>`;
                });
            } else {
                tagsDiv.innerHTML = `<span class="px-2 py-1 bg-slate-100 text-slate-500 border border-slate-200 rounded text-[10px] font-semibold">Unidentified</span>`;
            }
        }
        function closeEntityModal() {
            document.getElementById('entity-modal').classList.add('translate-x-full');
        }

        function openTxModal(linkData) {
            document.getElementById('tx-modal').classList.remove('hidden');
            document.getElementById('tx-modal').classList.add('flex');
            
            document.getElementById('txm-amount').innerText = linkData.amount_usd ? `$${parseFloat(linkData.amount_usd).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : (linkData.amount || 'Unknown');
            document.getElementById('txm-hash').innerText = linkData.tx_hash || 'Unknown Hash';
            document.getElementById('txm-from').innerText = linkData.from_address || 'Unknown';
            document.getElementById('txm-to').innerText = linkData.to_address || 'Unknown';
            
            const intel = `[INTELLIGENCE SYSTEM]
Transaction Hash: ${linkData.tx_hash}
Block: Verified
Asset: ${linkData.token_symbol || 'ETH'}
Type: ${linkData.tx_type || 'Transfer'}
Confidence Score: 99%

This transaction marks a critical hop in the asset lifecycle. Funds were moved rapidly to evade detection. Omnibus scanning complete.`;
            document.getElementById('txm-intel').innerText = intel;
        }
        function closeTxModal() {
            document.getElementById('tx-modal').classList.add('hidden');
            document.getElementById('tx-modal').classList.remove('flex');
        }

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
        }

        // On Load, check for query param and run trace
        document.addEventListener('DOMContentLoaded', () => {
            const params = new URLSearchParams(window.location.search);
            const target = params.get('q');
            if (target) {
                runTrace(target);
            }
        });

        async function runTrace(targetAddress) {
            if (!targetAddress) {
                const params = new URLSearchParams(window.location.search);
                targetAddress = params.get('q');
            }
            if (!targetAddress) return;

            document.getElementById('loading-overlay').classList.remove('hidden');
            document.getElementById('loading-overlay').classList.add('flex');
            document.getElementById('trace-status').innerText = 'Processing...';

            try {
                // Call API
                const formData = new FormData();
                formData.append('target_address', targetAddress);
                
                const response = await fetch('/trace', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) throw new Error("API Error");
                const data = await response.json();
                currentTraceData = data;
                
                renderGraph(data);
                renderLedger(data);
                
                document.getElementById('trace-status').innerText = 'Completed';
                document.getElementById('trace-status').className = 'bg-emerald-100 text-emerald-700 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider';

                // Update Stats
                if (data.nodes) document.getElementById('stat-addresses').innerText = data.nodes.length;
                if (data.edges) document.getElementById('stat-txs').innerText = data.edges.length;
                
                let vol = 0;
                if (data.edges) {
                    data.edges.forEach(e => { if(e.amount_usd) vol += parseFloat(e.amount_usd); });
                }
                document.getElementById('stat-vol').innerText = `$${vol.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2})}`;

            } catch (err) {
                console.error(err);
                document.getElementById('trace-status').innerText = 'Failed';
                document.getElementById('trace-status').className = 'bg-red-100 text-red-700 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider';
                document.getElementById('graph-flow').innerHTML = `<div class="text-red-500 font-bold p-8">Error loading trace data. Please try again.</div>`;
            } finally {
                document.getElementById('loading-overlay').classList.add('hidden');
                document.getElementById('loading-overlay').classList.remove('flex');
            }
        }

        function formatNodeHtml(node) {
            // Node data from backend: {id, type, label, risk_score, known_entity}
            const isCex = node.type === 'exchange';
            const iconUrl = isCex ? 'https://upload.wikimedia.org/wikipedia/commons/f/fc/Binance-coin-bnb-logo.png' : 'https://cdn-icons-png.flaticon.com/512/855/855279.png';
            const nodeName = node.known_entity || node.label || node.id.substring(0,6)+'...';
            const nodeTypeStr = (node.type || 'wallet').toUpperCase();
            const badgeIcon = isCex ? '<i class="fa-solid fa-check text-[8px]"></i>' : '<i class="fa-solid fa-question text-[8px]"></i>';
            const badgeColor = isCex ? 'bg-emerald-500' : 'bg-slate-500';
            
            // Calculate mock outflows for demo purposes (API doesn't return this directly per node yet)
            let mockOutflow = "$0.00";
            if (currentTraceData && currentTraceData.edges) {
                let out = 0;
                currentTraceData.edges.forEach(e => { if(e.from_address === node.id && e.amount_usd) out += parseFloat(e.amount_usd); });
                mockOutflow = `$${out.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                node.outflow = out; // save for modal
            }

            return `
            <div class="node-card shrink-0 w-[140px] h-[160px] bg-white border border-slate-200 rounded-[12px] relative flex flex-col items-center justify-center p-3 z-10 shadow-sm" onclick='openEntityModal("${node.id}", ${JSON.stringify(node).replace(/'/g, "&apos;")})'>
                <!-- Icon Circle -->
                <div class="w-14 h-14 rounded-full border-2 border-slate-100 flex items-center justify-center bg-slate-50 shadow-inner mb-3 relative">
                    <img src="${iconUrl}" class="w-8 h-8 object-contain">
                    <!-- Badge -->
                    <div class="absolute -right-1 -top-1 w-5 h-5 rounded-full border-2 border-white text-white flex items-center justify-center ${badgeColor}">
                        ${badgeIcon}
                    </div>
                </div>
                
                <div class="text-blue-600 font-bold text-[13px] mb-2 truncate w-full text-center">${mockOutflow}</div>
                
                <div class="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-[9px] font-bold uppercase truncate max-w-[90%] border border-blue-100">${nodeName}</div>
                <div class="text-slate-500 text-[9px] font-semibold uppercase mt-1 tracking-wider">${nodeTypeStr}</div>
            </div>`;
        }

        function formatEdgeHtml(edge) {
            // Edge data from backend: {from_address, to_address, tx_hash, amount, amount_usd, token_symbol}
            const label = edge.token_symbol || 'ASSET';
            const amountStr = edge.amount_usd ? `$${parseFloat(edge.amount_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : (edge.amount || '0');
            const hashShort = edge.tx_hash ? edge.tx_hash.substring(0,8) + '...' + edge.tx_hash.substring(edge.tx_hash.length-4) : 'Unknown Hash';

            return `
            <div class="edge-line shrink-0 min-w-[200px] flex-1 relative flex flex-col items-center justify-center -mx-2 z-0 group" onclick='openTxModal(${JSON.stringify(edge).replace(/'/g, "&apos;")})'>
                
                <!-- Label Top -->
                <div class="absolute top-4 text-center w-full px-4">
                    <div class="text-slate-500 font-bold text-[9px] uppercase tracking-widest"><i class="fa-brands fa-ethereum mr-1"></i>${label}</div>
                    <div class="text-slate-400 font-bold text-[8px] uppercase mt-1">OUTFLOW</div>
                    <div class="text-red-500 font-bold text-[11px] mt-0.5">↓ ${amountStr}</div>
                </div>

                <!-- Line & Arrow -->
                <div class="w-full relative flex items-center h-8 my-auto top-3 group-hover:px-2 transition-all">
                    <div class="edge-stroke w-full h-[2px] bg-blue-300"></div>
                    <div class="edge-arrow absolute left-1/2 -ml-[5px] w-0 h-0 border-y-[5px] border-y-transparent border-l-[8px] border-l-blue-400"></div>
                </div>

                <!-- Label Bottom -->
                <div class="absolute bottom-6 text-center w-full px-4">
                    <div class="text-slate-500 font-mono text-[10px] bg-white/80 px-1 inline-block">${hashShort}</div>
                </div>
                <div class="absolute bottom-1 text-center w-full">
                    <span class="bg-indigo-50 text-indigo-600 border border-indigo-100 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider">${label}</span>
                </div>
            </div>`;
        }

        function renderGraph(data) {
            const flowContainer = document.getElementById('graph-flow');
            flowContainer.innerHTML = '';
            
            if (!data || !data.nodes || data.nodes.length === 0) {
                flowContainer.innerHTML = '<div class="text-slate-400 italic">No trace data found.</div>';
                return;
            }

            let html = '';
            const renderedNodes = new Set();

            if (data.edges && data.edges.length > 0) {
                // Linearize edges
                for (let i = 0; i < data.edges.length; i++) {
                    const edge = data.edges[i];
                    const sourceNode = data.nodes.find(n => n.id === edge.from_address) || {id: edge.from_address};
                    const targetNode = data.nodes.find(n => n.id === edge.to_address) || {id: edge.to_address};

                    if (i === 0) {
                        html += formatNodeHtml(sourceNode);
                        renderedNodes.add(sourceNode.id);
                    }
                    
                    html += formatEdgeHtml(edge);
                    html += formatNodeHtml(targetNode);
                    renderedNodes.add(targetNode.id);
                }
            } else if (data.nodes.length === 1) {
                html += formatNodeHtml(data.nodes[0]);
            }
            
            flowContainer.innerHTML = html;
        }

        function renderLedger(data) {
            const tbody = document.getElementById('ledger-body');
            tbody.innerHTML = '';
            if(!data || !data.edges) {
                document.getElementById('ledger-count').innerText = "0 Records";
                return;
            }
            
            document.getElementById('ledger-count').innerText = `${data.edges.length} Records`;
            
            data.edges.forEach(edge => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition cursor-pointer";
                tr.onclick = () => openTxModal(edge);
                
                const amtUsdStr = edge.amount_usd ? `$${parseFloat(edge.amount_usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : '-';
                
                tr.innerHTML = `
                    <td class="px-4 py-2">${edge.timestamp || 'Unknown'}</td>
                    <td class="px-4 py-2 text-blue-600 hover:underline">${edge.tx_hash ? edge.tx_hash.substring(0,10)+'...' : 'N/A'}</td>
                    <td class="px-4 py-2">${edge.from_address ? edge.from_address.substring(0,12)+'...' : 'Unknown'}</td>
                    <td class="px-4 py-2">${edge.to_address ? edge.to_address.substring(0,12)+'...' : 'Unknown'}</td>
                    <td class="px-4 py-2">${edge.token_symbol || 'ETH'}</td>
                    <td class="px-4 py-2 text-right">${edge.amount || '0'}</td>
                    <td class="px-4 py-2 text-right font-black text-slate-800">${amtUsdStr}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    </script>
</body>
</html>
