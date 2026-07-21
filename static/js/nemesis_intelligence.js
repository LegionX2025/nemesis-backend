let ontologyData = [];
let universalMatrix = {};

function hideAllPages() {
    document.querySelectorAll('.doc-section').forEach(el => el.classList.add('hidden'));
    document.getElementById('universal-matrix-view').classList.add('hidden');
    document.getElementById('scenario-view').classList.add('hidden');
    
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
}

function showDocPage(pageId) {
    hideAllPages();
    const page = document.getElementById('page-' + pageId);
    if (page) page.classList.remove('hidden');
    
    const nav = document.querySelector(`.nav-item[data-target="${pageId}"]`);
    if (nav) nav.classList.add('active');
}

function showMatrix() {
    hideAllPages();
    document.getElementById('universal-matrix-view').classList.remove('hidden');
    
    const nav = document.querySelector(`.nav-item[data-target="matrix"]`);
    if (nav) nav.classList.add('active');
}

async function init() {
    try {
        const res = await fetch('/api/ontology');
        const data = await res.json();
        ontologyData = data.scenarios || [];
        universalMatrix = data.matrix || {};
        
        renderHierarchy();
        renderMatrix();
    } catch(e) {
        console.error("Failed to load ontology", e);
    }
}

function renderHierarchy() {
    const container = document.getElementById('hierarchy-container');
    container.innerHTML = '';
    
    // Group by Chain
    const grouped = {};
    ontologyData.forEach(scen => {
        if(!grouped[scen.chain]) grouped[scen.chain] = [];
        grouped[scen.chain].push(scen);
    });
    
    for(const chain in grouped) {
        let html = `
            <div class="mb-3">
                <div class="text-slate-800 font-bold uppercase tracking-wider text-[11px] flex items-center gap-2 mb-1">
                    <i class="fa-solid fa-link text-slate-400"></i> ${chain}
                </div>
                <div class="pl-3 space-y-1 border-l-2 border-slate-200 ml-1">
        `;
        
        grouped[chain].forEach(scen => {
            html += `
                <div class="cursor-pointer text-[11px] font-semibold text-slate-500 hover:text-blue-600 transition py-1 pl-2 hover:bg-slate-100 rounded" onclick="viewScenario('${scen.scenario_id}')">
                    <i class="fa-solid fa-file-alt mr-1 opacity-50"></i> ${scen.scenario_id.replace(/_/g, ' ')}
                </div>
            `;
        });
        
        html += `</div></div>`;
        container.innerHTML += html;
    }
}

function renderMatrix() {
    const tbody = document.getElementById('matrix-body');
    tbody.innerHTML = '';
    
    for(const [chain, obj] of Object.entries(universalMatrix)) {
        tbody.innerHTML += `
            <tr class="hover:bg-slate-50 transition">
                <td class="p-4 font-bold text-slate-900"><span class="chain-badge bg-white border border-slate-300 shadow-sm">${chain}</span></td>
                <td class="p-4"><span class="flow-node">${obj.Lock}</span></td>
                <td class="p-4"><span class="flow-node">${obj.Mint}</span></td>
                <td class="p-4"><span class="flow-node">${obj.Burn}</span></td>
                <td class="p-4"><span class="flow-node">${obj.Transfer}</span></td>
                <td class="p-4"><span class="flow-node bg-indigo-50 border-indigo-200 text-indigo-700">${obj.Bridge}</span></td>
                <td class="p-4"><span class="flow-node bg-rose-50 border-rose-200 text-rose-700">${obj.Exchange}</span></td>
            </tr>
        `;
    }
}

function viewScenario(id) {
    hideAllPages();
    document.getElementById('scenario-view').classList.remove('hidden');
    
    const scen = ontologyData.find(s => s.scenario_id === id);
    if(!scen) return;
    
    document.getElementById('scen-title').innerText = scen.scenario_id.replace(/_/g, ' ');
    document.getElementById('scen-chain').innerText = scen.chain;
    document.getElementById('scen-dest').innerText = scen.destination_chain;
    document.getElementById('scen-cat').innerText = scen.category;
    
    // Render Flow
    let flowArr = scen.flow.split('->').map(s=>s.trim());
    document.getElementById('scen-flow').innerHTML = flowArr.map((f, i) => 
        `<span class="font-bold ${i===0?'text-rose-600':i===flowArr.length-1?'text-emerald-600':'text-slate-700'}">${f}</span>`
    ).join(' <i class="fa-solid fa-arrow-right flow-arrow"></i> ');
    
    // Render State Transitions
    document.getElementById('scen-states').innerHTML = scen.state_transitions.map((s, i) => 
        `<span class="flow-node">${s}</span>`
    ).join(' <i class="fa-solid fa-link flow-arrow opacity-50"></i> ');
    
    // Render Fingerprints
    document.getElementById('scen-fingerprints').innerHTML = scen.fingerprints.map(f => 
        `<span class="bg-orange-100 text-orange-700 border border-orange-200 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">${f}</span>`
    ).join('');
    
    // Render Identity Signals
    document.getElementById('scen-identity').innerHTML = scen.identity_signals.map(s => `<li>${s}</li>`).join('');
    
    // Render Detection
    document.getElementById('scen-detection').innerHTML = scen.detection_logic.map(d => 
        `<tr><td class="py-2 font-mono text-blue-600 pr-4">${d.stage}</td><td class="py-2 text-slate-700">${d.detection}</td></tr>`
    ).join('');
    
    // Render Confidence
    document.getElementById('scen-confidence').innerHTML = Object.entries(scen.confidence_scoring).map(([k, v]) => 
        `<div class="flex justify-between items-center bg-white p-3 border border-slate-200 rounded shadow-sm">
            <span class="text-xs text-slate-600 font-bold">${k}</span>
            <span class="text-sm font-black ${v>=98?'text-emerald-600':v>=90?'text-blue-600':'text-amber-600'}">${v}%</span>
        </div>`
    ).join('');
}

const searchInput = document.getElementById('search-ontology');
if(searchInput) {
    searchInput.addEventListener('input', (e) => {
        const val = e.target.value.toLowerCase();
        if(val === '') renderHierarchy();
        else {
            // Filter hierarchy logic
        }
    });
}

document.addEventListener('DOMContentLoaded', init);
