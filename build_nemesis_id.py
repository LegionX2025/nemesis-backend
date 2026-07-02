import os
import re

def build():
    src = "templates/index.html"
    dest = "templates/nemesis_id.html"
    
    if not os.path.exists(src):
        print(f"Error: {src} not found.")
        return

    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Change title and branding
    content = content.replace("<title>Lionsgate Omni-Chain Forensics | Case LGN-US-2026-0172</title>", "<title>NEMESIS ID | Omni-Chain Identity Profiling</title>")
    content = content.replace("NEMESIS</h1", "NEMESIS ID</h1")
    content = content.replace("Omni-Chain Trace", "Identity Profiling")
    content = content.replace("START OMNICHAIN TRACE &rarr;", "GENERATE NEMESIS ID &rarr;")
    
    # 2. Update CSS for Light Theme
    # Remove dark theme classes and background colors
    content = content.replace("body { background-color: #0f172a; color: #f8fafc;", "body { background-color: #f1f5f9; color: #0f172a;")
    
    # Inject an AJAX Loader for propagation
    loader_html = """
    <!-- AJAX Loader -->
    <div id="ajax-loader" class="hidden fixed inset-0 z-[300] bg-white/90 backdrop-blur-md flex-col justify-center items-center transition-all duration-500">
        <div class="w-24 h-24 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-6 shadow-xl"></div>
        <h2 class="text-2xl font-black text-slate-800 tracking-widest uppercase mb-2">Propagating Identity</h2>
        <p class="text-slate-500 font-mono text-sm" id="ajax-loader-text">Cross-referencing OmniChain ledgers...</p>
    </div>
    """
    
    # Insert loader right after body starts
    content = content.replace('<body class="flex flex-col h-screen">', '<body class="flex flex-col h-screen theme-enterprise_light">\n' + loader_html)

    # 3. Strip out unwanted inputs for NEMESIS ID (Dates, Amounts, Multiple Addresses)
    # Landing page replacement
    landing_pattern = r'<div class="landing-input-group[^"]*">.*?</div>\s*</main>'
    new_landing = """<div class="landing-input-group">
                        <div>
                            <label>Target Wallet Address</label>
                            <input type="text" id="landing-seed-input" placeholder="Enter 0x... address" class="w-full bg-white border border-slate-200/20 rounded p-3 text-slate-700 font-mono focus:outline-none focus:border-blue-400 focus:bg-white/90 transition shadow-sm" style="background: rgba(255,255,255,0.7);">
                        </div>
                        <button class="landing-btn-primary" onclick="initiateLandingTrace()">GENERATE NEMESIS ID &rarr;</button>
                        
                        <!-- Hidden inputs to satisfy initiateLandingTrace JS requirements -->
                        <div class="hidden">
                            <input type="number" id="landing-target-amount" value="0">
                            <input type="date" id="landing-start-date">
                            <input type="date" id="landing-end-date">
                        </div>
                        
                        <div class="h-px bg-slate-200 w-full my-2"></div>
                        
                        <div>
                            <label>Nemesis ID Retrieval</label>
                            <div class="flex gap-2 mt-2">
                                <input type="text" id="landing-search-trace" placeholder="e.g. NID-XXXX" class="flex-grow w-full bg-white border border-slate-200/20 text-slate-700 font-mono focus:outline-none focus:border-blue-400 p-3 rounded-lg" style="background: rgba(255,255,255,0.7);">
                                <button class="landing-btn-primary !mt-0 px-6" onclick="fetchHistoricalTrace()">RETRIEVE</button>
                            </div>
                        </div>
                    </div>
                </main>"""
    content = re.sub(landing_pattern, new_landing, content, flags=re.DOTALL)
    
    # Trace Control Panel replacement
    # Convert textarea to input text for single wallet
    content = re.sub(r'<textarea id="seed-input"[^>]*>.*?</textarea>', '<input type="text" id="seed-input" class="w-full bg-slate-900 border border-slate-700 text-slate-300 font-mono focus:outline-none focus:border-blue-500 p-4 rounded-xl shadow-inner transition" placeholder="Enter Target Wallet Address (0x...)">', content, flags=re.DOTALL)
    content = content.replace('<span>Target Seed Wallets / TXs (One per line)</span>', '<span>Target Wallet Address</span>')
    
    # Remove Parameters div from trace dashboard for NEMESIS ID
    filters_pattern = r'<!-- Parameters -->.*?<!-- Primary Action Buttons -->'
    content = re.sub(filters_pattern, '<!-- Primary Action Buttons -->', content, flags=re.DOTALL)
    
    # Modify trace button text
    content = content.replace('<span>Start Trace</span>', '<span>Generate ID</span>')
    vanta_dark = """
                    VANTA.NET({
                        el: "#tsparticles",
                        mouseControls: true,
                        touchControls: true,
                        gyroControls: false,
                        minHeight: 200.00,
                        minWidth: 200.00,
                        scale: 1.00,
                        scaleMobile: 1.00,
                        color: 0x0284c7,
                        backgroundColor: 0x0f172a,
                        points: 12.00,
                        maxDistance: 20.00,
                        spacing: 20.00,
                        showDots: true
                    });
"""
    vanta_light = """
                    VANTA.NET({
                        el: "#tsparticles",
                        mouseControls: true,
                        touchControls: true,
                        gyroControls: false,
                        minHeight: 200.00,
                        minWidth: 200.00,
                        scale: 1.00,
                        scaleMobile: 1.00,
                        color: 0x3b82f6,
                        backgroundColor: 0xf8fafc,
                        points: 15.00,
                        maxDistance: 25.00,
                        spacing: 18.00,
                        showDots: true
                    });
"""
    if "VANTA.NET({" in content:
        # Regex replace the vanta init
        content = re.sub(r'VANTA\.NET\(\{[\s\S]*?\}\);', vanta_light.strip(), content)
    
    # 4. Modify submitTrace to show the AJAX loader before proceeding
    init_func_match = re.search(r'(async function submitTrace\(\)\s*\{|function submitTrace\(\)\s*\{)', content)
    if init_func_match:
        init_func = init_func_match.group(1)
        new_init_func = init_func + """
                document.getElementById('ajax-loader').classList.remove('hidden');
                document.getElementById('ajax-loader').classList.add('flex');
                
                // Simulate propagation delay for UI effect
                setTimeout(() => {
                    document.getElementById('ajax-loader-text').innerText = "Resolving Neural Graph Topology...";
                    setTimeout(() => {
                        document.getElementById('ajax-loader').classList.add('hidden');
                        document.getElementById('ajax-loader').classList.remove('flex');
                    }, 1500);
                }, 1500);
"""
        content = content.replace(init_func, new_init_func)
    
    # 5. Fix logo path in NEMESIS ID
    content = content.replace('src="/logo_nemesis.jpeg"', 'src="/static/logo_nemesis.jpeg"')

    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Successfully generated {dest} with Light Theme and AJAX Loader.")

if __name__ == "__main__":
    build()
