// Check Authentication First
const token = localStorage.getItem('nemesis_token');
if (!token) {
    window.location.href = '/login';
}

const baseUrl = window.location.origin;
const wsUrl = window.location.protocol === 'https:' ? `wss://${window.location.host}` : `ws://${window.location.host}`;
const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

function logout() {
    localStorage.removeItem('nemesis_token');
    window.location.href = '/login';
}

// Tab Switching
function switchTab(tabId) {
    const tabs = ['logs', 'cases', 'database', 'config', 'maintenance', 'engine'];
    const titles = {
        'logs': 'Live Console Logs',
        'cases': 'Case Management',
        'database': 'Database Statistics',
        'config': 'API Configuration',
        'maintenance': 'Godmode Auto-Pilot',
        'engine': 'Engine Controls'
    };

    tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        const view = document.getElementById(`view-${t}`);
        
        if (t === tabId) {
            btn.classList.add('active');
            btn.classList.remove('text-slate-500');
            view.classList.remove('hidden');
            view.classList.add('block');
        } else {
            btn.classList.remove('active');
            btn.classList.add('text-slate-500');
            view.classList.add('hidden');
            view.classList.remove('block');
        }
    });
    document.getElementById('header-title').innerText = titles[tabId];

    if (tabId === 'cases') fetchCases();
    if (tabId === 'database') fetchDbStats();
    if (tabId === 'config') fetchConfig();
}

// Module: Logs
function initLogsWS() {
    const ws = new WebSocket(`${wsUrl}/ws/admin/logs?token=${token}`);
    const consoleDiv = document.getElementById('log-console');
    if(!consoleDiv) return;
    ws.onmessage = (e) => {
        const span = document.createElement('div');
        span.textContent = e.data;
        // Basic color coding
        if (e.data.includes('ERROR')) span.className = 'text-red-400';
        else if (e.data.includes('WARNING')) span.className = 'text-amber-400';
        else if (e.data.includes('INFO')) span.className = 'text-blue-400';
        else span.className = 'text-slate-300';
        
        consoleDiv.appendChild(span);
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    };
    ws.onclose = () => {
        setTimeout(initLogsWS, 5000); // Reconnect
    };
    ws.onerror = () => {
        console.error("Log WebSocket Error");
    }
}

// Module: Cases
async function fetchCases() {
    try {
        const res = await fetch(`${baseUrl}/api/admin/cases`, { headers: authHeaders });
        if (res.status === 401) logout();
        const data = await res.json();
        
        const tbody = document.getElementById('cases-table');
        if(!tbody) return;
        if (!data.cases || data.cases.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="py-4 text-center text-slate-500 italic">No cases found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.cases.map(c => `
            <tr class="hover:bg-slate-50">
                <td class="py-3 px-2 font-mono text-blue-600">${c.case_id}</td>
                <td class="py-3 px-2 font-semibold text-slate-700">${c.name}</td>
                <td class="py-3 px-2"><span class="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-[10px] border border-emerald-200 font-bold">${c.status}</span></td>
                <td class="py-3 px-2 text-right"><button class="text-xs font-bold text-blue-500 hover:text-blue-700 border border-blue-200 bg-blue-50 px-3 py-1 rounded">View</button></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

// Module: Database
async function fetchDbStats() {
    try {
        const res = await fetch(`${baseUrl}/api/admin/db_stats`, { headers: authHeaders });
        const data = await res.json();
        const t1 = document.getElementById('stat-traces');
        if(t1) t1.innerText = data.traces || 0;
        const w1 = document.getElementById('stat-wallets');
        if(w1) w1.innerText = data.wallets || 0;
        const c1 = document.getElementById('stat-cases');
        if(c1) c1.innerText = data.cases || 0;
    } catch (e) {
        console.error(e);
    }
}

// Module: Config
async function fetchConfig() {
    try {
        const res = await fetch(`${baseUrl}/api/admin/config`, { headers: authHeaders });
        const data = await res.json();
        const configForm = document.getElementById('config-form');
        if(configForm) {
            configForm.innerHTML = `
                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Gemini API Key</label>
                    <input type="text" disabled value="${data.gemini_key || 'Not Set'}" class="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-500 text-sm font-mono shadow-inner cursor-not-allowed">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Etherscan API Key</label>
                    <input type="text" disabled value="${data.etherscan_key || 'Not Set'}" class="w-full bg-slate-50 border border-slate-200 rounded p-2 text-slate-500 text-sm font-mono shadow-inner cursor-not-allowed">
                </div>
            `;
        }
        const depth = document.getElementById('engine-depth');
        if(depth) depth.value = data.max_depth || 3;
        const hops = document.getElementById('engine-hops');
        if(hops) hops.value = data.max_hops || 50;
    } catch (e) {
        console.error(e);
    }
}

window.saveEngineConfig = async function() {
    const depthEl = document.getElementById('engine-depth');
    const hopsEl = document.getElementById('engine-hops');
    if(!depthEl || !hopsEl) return;
    const depth = parseInt(depthEl.value);
    const hops = parseInt(hopsEl.value);
    
    try {
        const res = await fetch(`${baseUrl}/api/admin/config`, {
            method: 'POST',
            headers: authHeaders,
            body: JSON.stringify({ gemini_key: "", etherscan_key: "", polygonscan_key: "", max_depth: depth, max_hops: hops })
        });
        if (res.ok) alert("Engine config updated.");
    } catch(e) {
        console.error(e);
    }
}

window.loadMaintenanceReports = async function() {
    const list = document.getElementById('maintenance-reports-list');
    if(!list) return;
    try {
        list.innerHTML = '<div class="text-center text-slate-400 text-sm py-10 italic">Loading reports...</div>';
        const res = await fetch(`${baseUrl}/api/admin/maintenance_reports`, { headers: authHeaders });
        const data = await res.json();
        
        if (!data.reports || data.reports.length === 0) {
            list.innerHTML = '<div class="text-center text-slate-400 text-sm py-10 italic">No maintenance reports found.</div>';
            return;
        }
        
        let html = '';
        data.reports.forEach(r => {
            const statusColor = r.status === 'PASS' ? 'text-green-600 bg-green-50 border-green-200' : 'text-red-600 bg-red-50 border-red-200';
            const icon = r.status === 'PASS' ? 'fa-check-circle' : 'fa-triangle-exclamation';
            
            html += `
                <div class="border border-slate-200 rounded-lg overflow-hidden bg-white">
                    <div class="p-4 flex justify-between items-center cursor-pointer hover:bg-slate-50 transition" onclick="this.nextElementSibling.classList.toggle('hidden')">
                        <div class="flex items-center gap-4">
                            <span class="px-3 py-1 rounded text-[10px] font-bold uppercase tracking-wider border ${statusColor}">
                                <i class="fa-solid ${icon} mr-1"></i> ${r.status || 'UNKNOWN'}
                            </span>
                            <span class="font-mono text-sm text-slate-600">${r.report_id || 'ID'}</span>
                            <span class="text-xs text-slate-400"><i class="fa-regular fa-clock mr-1"></i> ${new Date(r.timestamp).toLocaleString()}</span>
                        </div>
                        <i class="fa-solid fa-chevron-down text-slate-400 text-xs"></i>
                    </div>
                    <div class="hidden border-t border-slate-200 bg-slate-50 p-4">
                        <h4 class="text-xs uppercase tracking-widest font-bold text-purple-700 mb-2"><i class="fa-solid fa-robot mr-1"></i> Godmode AI Analysis</h4>
                        <div class="prose prose-sm prose-slate max-w-none bg-white p-4 border border-purple-100 rounded mb-4 shadow-sm" style="white-space: pre-wrap; font-family: monospace; font-size: 11px;">${r.ai_analysis || 'No analysis available.'}</div>
                        
                        <h4 class="text-xs uppercase tracking-widest font-bold text-slate-700 mb-2"><i class="fa-solid fa-terminal mr-1"></i> Raw Execution Logs</h4>
                        <pre class="bg-slate-900 text-slate-300 p-4 rounded text-[10px] font-mono overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">${r.raw_logs || 'No logs recorded.'}</pre>
                    </div>
                </div>
            `;
        });
        list.innerHTML = html;
    } catch (e) {
        console.error(e);
        list.innerHTML = '<div class="text-center text-red-500 text-sm py-10 font-bold">Failed to load reports.</div>';
    }
}

window.triggerMaintenanceRun = async function() {
    if(!confirm("Are you sure you want to trigger a full system diagnostic? This will take a few minutes.")) return;
    try {
        const res = await fetch(`${baseUrl}/api/admin/maintenance/run`, { method: 'POST', headers: authHeaders });
        const data = await res.json();
        alert(data.status || "Maintenance task initiated.");
        setTimeout(window.loadMaintenanceReports, 5000);
    } catch (e) {
        console.error(e);
        alert("Failed to trigger maintenance task.");
    }
}

// Expose these globally if needed by onclick inline attributes
window.switchTab = switchTab;
window.logout = logout;

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initLogsWS();
        window.loadMaintenanceReports();
    });
} else {
    initLogsWS();
    window.loadMaintenanceReports();
}
