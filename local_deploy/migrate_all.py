import os
import shutil
import re

mock_dir = r"C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts\Advanced_Mock_Simulations\Enterprise_Starry_Flow_Mocks"
frontend_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

print("Starting complete redesign migration & API integration...")

# 1. Copy Assets
assets_src = os.path.join(mock_dir, "assets")
assets_dst = os.path.join(frontend_dir, "assets")
if os.path.exists(assets_src):
    if not os.path.exists(assets_dst):
        shutil.copytree(assets_src, assets_dst)
    else:
        for item in os.listdir(assets_src):
            s = os.path.join(assets_src, item)
            d = os.path.join(assets_dst, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

# 1.5 Copy new LOGO.jpeg
new_mock_dir = os.path.join(mock_dir, "new_mock")
logo_src = os.path.join(new_mock_dir, "LOGO.jpeg")
logo_dst = os.path.join(frontend_dir, "assets", "LOGO.jpeg")
if os.path.exists(logo_src):
    shutil.copy2(logo_src, logo_dst)

# 2. Process nemesis_id.html
src_id = os.path.join(mock_dir, "nemesis_id.html")
dst_id = os.path.join(frontend_dir, "nemesis_id.html")
if os.path.exists(src_id):
    with open(src_id, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace startDataFetch with executeSearch
    content = content.replace('onclick="startDataFetch()"', 'onclick="executeSearch()"')

    # Remove mock data placeholders
    content = content.replace('>--<', '>-<') # Keep dashes but clear mock formatting if any
    
    api_script = """
    <script>
        async function executeSearch() {
            const input = document.getElementById('search-input');
            if(!input) return;
            const address = input.value.trim();
            if(!address) {
                alert("Please enter a target wallet address.");
                return;
            }

            const loader = document.getElementById('main-loader');
            if(loader) loader.classList.remove('hidden');

            try {
                const backendUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8088' : '';
                
                const [walletRes, osintRes, geoRes, aiRes] = await Promise.all([
                    fetch(`${backendUrl}/api/wallet_profile/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/osint/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/nemesis_id/georisk/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/nemesis_id/ai_insights/${address}`).catch(() => null)
                ]);

                const walletData = walletRes ? await walletRes.json() : {};
                const osintData = osintRes ? await osintRes.json() : {};
                const geoData = geoRes ? await geoRes.json() : {};
                const aiData = aiRes ? await aiRes.json() : {};

                // Update UI elements
                if(document.getElementById('header-address')) document.getElementById('header-address').textContent = address;
                if(document.getElementById('prof-in')) document.getElementById('prof-in').textContent = `$${(walletData.usd_value || 0).toLocaleString()}`;
                
                const txTable = document.getElementById('table-transactions');
                if(txTable && walletData.transactions) {
                    txTable.innerHTML = '';
                    walletData.transactions.forEach(tx => {
                        txTable.innerHTML += `<tr>
                            <td class="py-3 px-4">${tx.date}</td>
                            <td class="py-3 px-4 font-mono">${tx.hash.substring(0, 8)}...</td>
                            <td class="py-3 px-4">${tx.type}</td>
                            <td class="py-3 px-4">${tx.from_to}</td>
                            <td class="py-3 px-4 text-right">${tx.value}</td>
                        </tr>`;
                    });
                }
            } catch(e) {
                console.error("Fetch error:", e);
                alert("Failed to connect to NEMESIS Backend API.");
            } finally {
                if(loader) loader.classList.add('hidden');
            }
        }
    </script>
    """
    if "executeSearch()" not in content.split("function switchTab")[0]: # Basic check
        content = content.replace("</body>", f"{api_script}\n</body>")
        
    with open(dst_id, "w", encoding="utf-8") as f:
        f.write(content)

# 3. Process nemesis_tracer.html
src_tracer = os.path.join(mock_dir, "nemesis_tracer.html")
dst_tracer = os.path.join(frontend_dir, "nemesis_tracer.html")
if os.path.exists(src_tracer):
    with open(src_tracer, "r", encoding="utf-8") as f:
        content = f.read()

    tracer_script = """
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const backendUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8088' : '';
            const socket = io(backendUrl);
            
            socket.on('connect', () => console.log('Connected to Tracer Socket'));
            
            socket.on('LEDGER_BATCH', (data) => {
                const tbody = document.getElementById('ledger-tbody');
                if(tbody) {
                    // Remove placeholder
                    if(tbody.innerHTML.includes('No trace active')) tbody.innerHTML = '';
                    
                    data.forEach(tx => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td class="py-3 px-4">${tx.hash.substring(0, 10)}...</td>
                                        <td class="py-3 px-4">${tx.from} -> ${tx.to}</td>
                                        <td class="py-3 px-4 text-emerald-600">${tx.value}</td>`;
                        tbody.prepend(tr);
                    });
                }
            });

            window.startTrace = function() {
                const address = prompt("Enter target wallet address to trace:");
                if(address) socket.emit('START_TRACE', { address });
            };
        });
    </script>
    """
    
    # Strip mock ledger
    content = content.replace('<!-- Mock Data Rows -->', '')
    content = content.replace('<tr><td colspan="5" class="py-8 text-center text-slate-400 italic">No trace active. System standing by.</td></tr>', '')
    
    # Inject socket.io
    content = content.replace("</body>", f"{tracer_script}\n</body>")
    
    # Bind start button
    content = content.replace('Start Neural Trace', 'Start Neural Trace" onclick="startTrace()')
    
    with open(dst_tracer, "w", encoding="utf-8") as f:
        f.write(content)

# 4. Process remaining files and strip mock data
html_files = ["nemesis_intelligence.html", "recovery_framework.html", "intro.html"]
for file in html_files:
    src = os.path.join(mock_dir, file)
    dst = os.path.join(frontend_dir, file)
    if os.path.exists(src):
        with open(src, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Strip specific mock data if present
        if file == "nemesis_intelligence.html":
            content = content.replace("LAZARUS GROUP", "")
            content = content.replace("99.9% CONFIDENCE", "Awaiting Target")
            # Clear mock lists
            content = re.sub(r'<ul id="osint-list".*?</ul>', '<ul id="osint-list" class="space-y-2"></ul>', content, flags=re.DOTALL)
            
        elif file == "recovery_framework.html":
            # Clear mock case logs
            content = re.sub(r'<div id="case-logs".*?</div>', '<div id="case-logs" class="p-4">No active cases.</div>', content, flags=re.DOTALL)

        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)

print("Migration and Integration Completed Successfully.")
