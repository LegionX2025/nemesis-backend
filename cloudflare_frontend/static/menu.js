// menu.js - Global Navigation & Modal Injection for Lionsgate Nemesis

document.addEventListener("DOMContentLoaded", () => {
    // 1. Inject Global Header
    const headerHTML = `
        <header class="bg-slate-900 text-white border-b border-slate-800 flex flex-col z-20 shrink-0 shadow-md">
            <div class="px-6 py-3 flex justify-between items-center w-full">
                <div class="flex items-center gap-4">
                    <img src="/static/logo_nemesis.jpeg" alt="Nemesis Logo" class="h-9 w-9 rounded border border-slate-700 shadow-sm cursor-pointer" onclick="window.location.href='/'">
                    <div>
                        <h1 class="text-lg font-black uppercase tracking-widest text-slate-100 leading-tight cursor-pointer" onclick="window.location.href='/'">Lionsgate Nemesis</h1>
                        <p class="text-[10px] text-blue-400 font-mono font-bold uppercase tracking-widest leading-none mt-1">Omni-Chain Trace Stream</p>
                    </div>
                    
                    <div class="h-8 w-px bg-slate-700 mx-4"></div>
                    
                    <!-- Global Links -->
                    <div class="flex items-center gap-4 text-xs font-bold uppercase tracking-wider">
                        <a href="/nemesis_tracer.html" class="hover:text-blue-400 transition"><i class="fa-solid fa-microchip text-indigo-400"></i> Tracer</a>
                        <a href="/nemesis_id.html" class="hover:text-fuchsia-400 transition"><i class="fa-solid fa-id-card text-fuchsia-400"></i> Nemesis ID</a>
                        <a href="/darknet_search.html" class="hover:text-purple-400 transition"><i class="fa-solid fa-user-secret text-purple-400"></i> Darknet Intel</a>
                        <a href="/darknet_live.html" class="hover:text-red-400 transition"><i class="fa-solid fa-chart-network text-red-400"></i> Live Graph</a>
                    </div>
                </div>

                <!-- Global Actions -->
                <div class="flex items-center gap-3">
                    <a href="/audit" class="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded-md text-[11px] font-bold shadow transition flex items-center gap-2 no-underline">
                        <i class="fa-solid fa-shield-halved"></i> Master Audit
                    </a>
                    <a href="/intelligence" class="bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-md text-[11px] font-bold shadow transition flex items-center gap-2 no-underline">
                        <i class="fa-solid fa-brain"></i> Intelligence Base
                    </a>
                    <button onclick="openApiDocs()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-md text-[11px] font-bold shadow transition flex items-center gap-2">
                        <i class="fa-solid fa-code"></i> Enterprise API
                    </button>
                    <select id="global-theme-selector" onchange="applyGlobalTheme(this.value)" class="bg-slate-800 border border-slate-700 text-slate-300 px-2 py-1.5 rounded-md text-[11px] font-bold shadow transition outline-none cursor-pointer">
                        <option value="enterprise_light">Enterprise Light</option>
                        <option value="cyberpunk_dark">Cyberpunk Dark</option>
                        <option value="glassmorphism_ocean">Glass Ocean</option>
                    </select>
                </div>
            </div>
        </header>
    `;

    // Prepend header to body
    document.body.insertAdjacentHTML('afterbegin', headerHTML);

    // 2. Inject Modal Container
    const modalHTML = `
        <div id="global-content-modal" class="hidden fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[9999] items-center justify-center font-sans">
            <div class="bg-white rounded-xl shadow-2xl w-[800px] border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
                <div class="bg-indigo-600 text-white px-6 py-4 flex justify-between items-center shadow-sm">
                    <h2 class="text-lg font-bold flex items-center gap-2" id="global-content-modal-title">
                        Title
                    </h2>
                    <button onclick="closeGlobalModal()" class="text-indigo-200 hover:text-white transition"><i class="fa-solid fa-times"></i></button>
                </div>
                <div class="p-6 overflow-y-auto text-slate-700 text-sm" id="global-content-modal-body">
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Try setting theme if previously stored
    const savedTheme = localStorage.getItem('nemesis_theme') || 'enterprise_light';
    const selector = document.getElementById('global-theme-selector');
    if (selector) selector.value = savedTheme;
    applyGlobalTheme(savedTheme);
});

function openGlobalModal(title, htmlContent) {
    document.getElementById('global-content-modal-title').innerText = title;
    document.getElementById('global-content-modal-body').innerHTML = htmlContent;
    document.getElementById('global-content-modal').classList.remove('hidden');
    document.getElementById('global-content-modal').classList.add('flex');
}

function closeGlobalModal() {
    document.getElementById('global-content-modal').classList.add('hidden');
    document.getElementById('global-content-modal').classList.remove('flex');
}

// Full API Documentation Data
const enterpriseApiDocs = `
    <div class="space-y-6">
        <p class="text-slate-600 font-sans leading-relaxed">
            Welcome to the <strong>Lionsgate Nemesis Omni-Chain Intelligence API</strong>. 
            This documentation covers the endpoints for initiating omni-chain tracing, accessing the structured intelligence base, and querying the autonomous darknet spidering engine.
        </p>

        <!-- Core Tracing API -->
        <div class="bg-slate-50 border border-slate-200 rounded-lg p-5">
            <h3 class="font-bold text-indigo-700 text-lg mb-3 flex items-center gap-2"><i class="fa-solid fa-microchip"></i> Core Tracing API</h3>
            
            <div class="space-y-4">
                <div>
                    <h4 class="font-bold text-slate-800 font-mono text-sm">POST /api/start_trace</h4>
                    <p class="text-xs text-slate-600 mt-1 mb-2">Initializes a new OmniChain trace sequence.</p>
                    <pre class="text-xs bg-slate-800 text-slate-200 p-2 rounded overflow-x-auto">Payload: { "seeds": "0x...", "target_amount": "100", "target_currency": "USD", "max_depth": 12 }</pre>
                </div>
                <div class="border-t border-slate-200 pt-3">
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /ws/{trace_id}</h4>
                    <p class="text-xs text-slate-600 mt-1">WebSocket connection for streaming real-time graph block payloads and physics mutations.</p>
                </div>
                <div class="border-t border-slate-200 pt-3">
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /api/nemesis_id/search?query={id}</h4>
                    <p class="text-xs text-slate-600 mt-1">Fetches a completed historical trace ledger by Nemesis Trace ID.</p>
                </div>
                <div class="border-t border-slate-200 pt-3">
                    <h4 class="font-bold text-slate-800 font-mono text-sm">POST /api/deep_evidence</h4>
                    <p class="text-xs text-slate-600 mt-1 mb-2">Executes a deep AI-assisted forensic analysis on a specific transaction utilizing Gemini models and the 4byte signature directory.</p>
                    <pre class="text-xs bg-slate-800 text-slate-200 p-2 rounded overflow-x-auto">Payload: { "tx": "0x...", "chain": "ETH", "amount": "1.0", ... }</pre>
                </div>
            </div>
        </div>

        <!-- Darknet Intelligence API -->
        <div class="bg-slate-50 border border-slate-200 rounded-lg p-5">
            <h3 class="font-bold text-purple-700 text-lg mb-3 flex items-center gap-2"><i class="fa-solid fa-user-secret"></i> Darknet Intelligence API</h3>
            <div class="space-y-4">
                <div>
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /api/darknet/search?q={query}</h4>
                    <p class="text-xs text-slate-600 mt-1">Executes a dual-collection search returning both unstructured deep-web scrapes and structured VASP/Entity intelligence profiles.</p>
                </div>
                <div class="border-t border-slate-200 pt-3">
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /ws/darknet/stream</h4>
                    <p class="text-xs text-slate-600 mt-1">Server-Sent Events (SSE) proxy streaming real-time darknet discoveries, relationships, and Named Entity Recognition (NER) outputs.</p>
                </div>
            </div>
        </div>

        <!-- Admin & Operations API -->
        <div class="bg-slate-50 border border-slate-200 rounded-lg p-5">
            <h3 class="font-bold text-emerald-700 text-lg mb-3 flex items-center gap-2"><i class="fa-solid fa-shield-halved"></i> Administration API</h3>
            <div class="space-y-4">
                <div>
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /api/admin/cases</h4>
                    <p class="text-xs text-slate-600 mt-1">Retrieves active investigation case files and statuses.</p>
                </div>
                <div class="border-t border-slate-200 pt-3">
                    <h4 class="font-bold text-slate-800 font-mono text-sm">GET /api/admin/db_stats</h4>
                    <p class="text-xs text-slate-600 mt-1">Returns detailed MongoDB cluster, index, and collection performance metrics.</p>
                </div>
            </div>
        </div>
    </div>
`;

function openApiDocs() {
    openGlobalModal("Enterprise API Documentation", enterpriseApiDocs);
}

// Global Theme Applicator
function applyGlobalTheme(theme) {
    localStorage.setItem('nemesis_theme', theme);
    // Since we are standardizing on Light Theme with Web3GL per the plan, 
    // we'll inject the specific Light Theme rules to the body here if selected.
    
    // Fallback trigger if the original application has specific theme logic
    if (typeof applyTheme === 'function') {
        try { applyTheme(theme); } catch(e) {}
    }
}
