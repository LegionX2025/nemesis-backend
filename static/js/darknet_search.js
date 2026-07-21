// --- SEARCH FUNCTIONALITY ---
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;

    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('resultsContainer');
    
    loading.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    resultsContainer.innerHTML = '';

    try {
        const response = await fetch('/api/darknet/search?q=' + encodeURIComponent(query));
        const data = await response.json();

        if (data.error || data.status === 'error') {
            resultsContainer.innerHTML = `<div class="glass-panel p-6 text-red-600 font-bold">Error: ${data.message || data.error}</div>`;
        } else if (data.results && data.results.length > 0) {
            let html = `<div class="glass-text-container mb-4"><h2 class="text-xl font-bold text-slate-800">Found ${data.results.length} Intel Records</h2></div>`;
            
            data.results.forEach((doc, index) => {
                const web = doc.web_info || {};
                const title = web.title || 'Untitled Onion Site';
                const url = web.url || 'Unknown URL';
                const content = web.content || '';
                const shortContent = content.substring(0, 300) + (content.length > 300 ? '...' : '');
                
                const sanitizeHtml = (str) => {
                    const temp = document.createElement('div');
                    temp.textContent = str;
                    return temp.innerHTML;
                };
                const fullContentHtml = sanitizeHtml(content).replace(/\n/g, '<br>');
                
                let entitiesHtml = '';
                let fullEntitiesHtml = '';
                if (doc.uie_entities && doc.uie_entities.length > 0) {
                    const uniqueEntities = [...new Set(doc.uie_entities.map(e => e.value))].slice(0, 5);
                    entitiesHtml = `<div class="mt-3 flex flex-wrap gap-2">
                        ${uniqueEntities.map(e => `<span class="px-2 py-1 bg-emerald-100 text-emerald-700 border border-emerald-300 rounded text-[10px] uppercase font-bold tracking-wider">${sanitizeHtml(e)}</span>`).join('')}
                    </div>`;
                    
                    const allEntitiesHtml = doc.uie_entities.map(e => `
                        <div class="flex justify-between items-center bg-slate-50 border border-slate-200 p-3 rounded text-xs">
                            <span class="text-slate-500 font-bold uppercase tracking-widest text-[10px]">${sanitizeHtml(e.label || 'ENTITY')}</span>
                            <span class="text-blue-600 font-mono font-bold">${sanitizeHtml(e.value)}</span>
                        </div>
                    `).join('');
                    fullEntitiesHtml = `<div class="mt-6"><h4 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-200 pb-2 flex items-center gap-2"><i class="fa-solid fa-list-check text-blue-500"></i> Extracted Entities</h4><div class="grid grid-cols-1 md:grid-cols-2 gap-3">${allEntitiesHtml}</div></div>`;
                }
                
                let keywordsHtml = '';
                if (doc.keywords_detected && doc.keywords_detected.length > 0) {
                     keywordsHtml = `<div class="mt-6"><h4 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-200 pb-2 flex items-center gap-2"><i class="fa-solid fa-tags text-purple-500"></i> Target Keywords</h4>
                     <div class="flex flex-wrap gap-2">
                        ${doc.keywords_detected.map(k => `<span class="px-2 py-1 bg-purple-100 text-purple-700 border border-purple-300 rounded text-xs font-mono">${sanitizeHtml(k)}</span>`).join('')}
                     </div></div>`;
                }

                html += `
                <div class="glass-panel transition-all duration-300 hover:border-blue-300 mb-6 overflow-hidden">
                    <!-- Collapsed View / Header -->
                    <div class="p-6 cursor-pointer flex flex-col hover:bg-slate-50/50 transition-colors relative group" onclick="toggleExpand('result-${index}')">
                        <div class="absolute right-6 top-6 opacity-0 group-hover:opacity-100 transition-opacity">
                            <span class="text-[10px] font-bold text-blue-600 uppercase tracking-widest border border-blue-300 rounded px-2 py-1 flex items-center gap-1 bg-blue-50">
                                Click to Expand <i class="fa-solid fa-chevron-down"></i>
                            </span>
                        </div>
                        
                        <div class="flex justify-between items-start mb-3 pr-32">
                            <h3 class="text-xl font-black text-slate-900 truncate">${sanitizeHtml(title)}</h3>
                        </div>
                        <div class="text-sm text-purple-600 mb-4 block truncate font-mono flex items-center gap-2">
                            <i class="fa-solid fa-link text-slate-400"></i>
                            ${sanitizeHtml(url)}
                        </div>
                        <div class="flex justify-between items-end">
                            <div class="flex-1">
                                <p id="short-content-${index}" class="text-slate-600 text-sm leading-relaxed border-l-2 border-slate-300 pl-3 italic">${sanitizeHtml(shortContent)}</p>
                                <div id="short-entities-${index}">
                                    ${entitiesHtml}
                                </div>
                            </div>
                            <span class="text-[10px] font-mono text-slate-500 whitespace-nowrap bg-slate-100 px-3 py-1.5 rounded border border-slate-200 ml-4">${sanitizeHtml(doc.crawled_at) || 'Recent'}</span>
                        </div>
                    </div>
                    
                    <!-- Expanded View -->
                    <div id="result-${index}" class="hidden border-t border-slate-200 bg-white/80 p-6">
                        <h4 class="text-[10px] font-bold text-emerald-600 uppercase tracking-widest mb-3 border-b border-slate-200 pb-2 flex items-center gap-2">
                            <i class="fa-solid fa-file-lines"></i> Raw Intercepted Content
                        </h4>
                        <div class="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap font-mono bg-slate-50 p-5 rounded border border-slate-200 max-h-96 overflow-y-auto mb-6 shadow-inner">
${fullContentHtml}
                        </div>
                        
                        ${fullEntitiesHtml}
                        ${keywordsHtml}
                        
                        <div class="mt-8 flex justify-between items-center border-t border-slate-200 pt-5">
                            <span class="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Database ID: ${sanitizeHtml(doc['hash-ID'] || 'UNKNOWN')}</span>
                            <a href="${sanitizeHtml(url)}" target="_blank" class="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-bold uppercase tracking-widest transition-all flex items-center gap-2 shadow-md">
                                Access Live Node <i class="fa-solid fa-external-link-alt"></i>
                            </a>
                        </div>
                    </div>
                </div>
                `;
            });
            resultsContainer.innerHTML = html;
        } else {
            resultsContainer.innerHTML = `<div class="glass-panel p-6 text-slate-600 text-center font-bold">No intel records found matching your query.</div>`;
        }
    } catch (err) {
        resultsContainer.innerHTML = `<div class="glass-panel p-6 text-red-600 font-bold">Network Error: Could not connect to Darknet index.</div>`;
    }

    loading.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
}

const searchInput = document.getElementById('searchInput');
if(searchInput) {
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') performSearch();
    });
}

function toggleExpand(id) {
    const el = document.getElementById(id);
    const index = id.split('-')[1];
    const shortContent = document.getElementById('short-content-' + index);
    const shortEntities = document.getElementById('short-entities-' + index);
    
    if (el.classList.contains('hidden')) {
        el.classList.remove('hidden');
        shortContent.classList.add('hidden');
        if (shortEntities) shortEntities.classList.add('hidden');
    } else {
        el.classList.add('hidden');
        shortContent.classList.remove('hidden');
        if (shortEntities) shortEntities.classList.remove('hidden');
    }
}

// --- LIVE STREAM WEBSOCKET ---
let ws = null;
function toggleStreamPanel() {
    const panel = document.getElementById('live-stream-panel');
    panel.classList.toggle('active');
    
    if (panel.classList.contains('active')) {
        connectStream();
    } else {
        if (ws) {
            ws.close();
            ws = null;
        }
        updateStatus('Disconnected', false);
    }
}

function updateStatus(text, isConnected) {
    const statusEl = document.getElementById('stream-status');
    if (isConnected) {
        statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> <span class="text-emerald-500">${text}</span>`;
    } else {
        statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-500"></span> <span class="text-red-500">${text}</span>`;
    }
}

function connectStream() {
    if (ws) return;
    
    updateStatus('Connecting...', false);
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/darknet/stream`;
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            updateStatus('Live', true);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                appendStreamData(data);
            } catch (e) {
                console.error('Failed to parse stream data:', e);
            }
        };
        
        ws.onclose = () => {
            ws = null;
            const panel = document.getElementById('live-stream-panel');
            if (panel && panel.classList.contains('active')) {
                updateStatus('Reconnecting...', false);
                setTimeout(connectStream, 3000);
            }
        };
        
        ws.onerror = (err) => {
            console.error("Stream error:", err);
            if(ws) ws.close();
        };
    } catch (err) {
        console.error("Failed to connect WebSocket", err);
        updateStatus('Error', false);
    }
}

function appendStreamData(data) {
    const tbody = document.getElementById('stream-body');
    const tr = document.createElement('tr');
    tr.className = "border-b border-slate-100 hover:bg-slate-50 transition";
    
    const time = new Date().toLocaleTimeString();
    
    // Limit title/url length
    const url = data.url ? data.url.substring(0, 30) + '...' : 'N/A';
    const title = data.title ? data.title.substring(0, 50) + (data.title.length > 50 ? '...' : '') : 'Discovered Node';
    
    tr.innerHTML = `
        <td class="p-2 text-slate-500">${time}</td>
        <td class="p-2 text-blue-600 truncate max-w-[100px]" title="${data.url || ''}">${url}</td>
        <td class="p-2 text-slate-800 font-bold truncate max-w-[150px]">${title}</td>
    `;
    
    tbody.insertBefore(tr, tbody.firstChild);
    
    // Keep only last 100 entries to prevent memory leak
    if (tbody.children.length > 100) {
        tbody.removeChild(tbody.lastChild);
    }
}
