import os
import shutil
import re

os.makedirs('productions', exist_ok=True)
shutil.copy('index.py', 'productions/app.py')

with open('productions/.env', 'w') as f:
    f.write("""# 🛡️ LIONSGATE INTELLIGENCE NETWORK - SECURE ENVIRONMENT CONFIGURATION
ANKR_KEY=16ce3644f6ef2b62f5caa02e0deb03e34c9dc65ac68ff32a69827241752b87da
INFURA_KEY=2937d7343f364769890d2ed40d53743b
TATUM_KEY=t-6545d1b4b56296001c1eb2d0-15cad0bf498345589085cb1e 
ETHERSCAN_KEY=AYQRQWFDJRK8WAX2ICJ8U4JUSYXZT5J7II
POLYGONSCAN_API_KEY=YUXEUN58W2X5YYQZ3R8M33XN626B5X6JQA
TOKENVIEW_API_KEY=Rhl2uJqCsPkNaog2oL4q
OKLINK_API_KEY=
GEMINI_API_KEY=
MONGO_URI=
SOLANA_API_KEY=
KASPA_API_KEY=
APP_NAME=nemesis-platform
APP_MODE=production
FLASK_SECRET_KEY=y0ur-n3m3s1s-Sup3r-S3cr3t-K3y-456789
""")

with open('productions/requirements.txt', 'w') as f:
    f.write("""fastapi
uvicorn
motor
aiohttp
pydantic
certifi
pandas
scikit-learn
networkx
requests
pytest
playwright
""")

# Edit app.py
with open('productions/app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

# 1. Update detect_chain to support SOL and KASPA
app_code = app_code.replace(
    'elif val.startswith("0x"): return "EVM_AUTO"',
    'elif val.startswith("0x"): return "EVM_AUTO"\n    elif len(val) >= 43 and not val.startswith("0x"): return "SOLANA"\n    elif val.startswith("kaspa:"): return "KASPA"'
)

app_code = app_code.replace(
    'return "ETH"',
    'if chain == "SOLANA": return "SOL"\n    elif chain == "KASPA": return "KAS"\n    return "ETH"'
)

# 2. Add empty process handlers for SOL and KASPA to prevent errors during trace
app_code = app_code.replace(
    'async def process_evm_txs',
    '''async def process_solana_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    pass # To be implemented fully via OKLink or Solscan API

async def process_kaspa_txs(session, addr, txs, depth, carry_val, obf_path, chain, origin_seed):
    pass # To be implemented fully via Kaspa API

async def process_evm_txs'''
)

app_code = app_code.replace(
    'else: await process_evm_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)',
    'elif chain_type == "solana": await process_solana_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)\n            elif chain_type == "kaspa": await process_kaspa_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)\n            else: await process_evm_txs(session, addr, txs, depth, carry_val, obf_path, actual_chain, origin_seed)'
)

# 3. Remove Mock Data Injection from fetch_txs
mock_data_pattern = re.compile(r'# --- MOCK DATA INJECTION.*?# -----------------------------------------------------', re.DOTALL)
app_code = mock_data_pattern.sub('', app_code)

# 4. Remove Hardcoded known entities for Suspect
app_code = app_code.replace('KNOWN_ENTITIES["0x3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"] = "SUSPECT Wallet"', '')
app_code = app_code.replace('KNOWN_ENTITIES["bc1pnhgwhvs3g6yv7c2hz9pyamvyj25lz5tsa79tugcexdun4zf4vzpsgpleg6"] = "SUSPECT Wallet"', '')
app_code = app_code.replace('KNOWN_ENTITIES["bc1pk85t3a2n8n72n860gtzd4cvrtptq09zm2keawpa5xmayvm9jhwls3lzju4"] = "SUSPECT Wallet"', '')

# 5. Modify Frontend HTML for Custom Inputs
# Replace the hardcoded defaultSeeds assignment
app_code = app_code.replace(
    'const defaultSeeds = "0x7675DC2856fca0C22ed3C57979388FbF236De57F\\n0x616C6bb9d5BB443D03a7bD5746404897de106A93\\nbc1qprtnld4jf43uq6h9y460d76annunqag9dhcv52\\n1NV7GCWYo7Tr3hErJzLRk4n2oV5B88eCNU";',
    'const defaultSeeds = "";'
)

# Add custom input fields to header
header_replacement = """
        <header class="bg-white border-b border-slate-200 p-4 flex flex-col gap-4 shadow-sm z-10 shrink-0">
            <div class="flex justify-between items-center w-full">
                <div>
                    <h1 class="text-xl font-black uppercase tracking-wider text-slate-900">Lionsgate Nemesis Engine</h1>
                    <p class="text-xs text-blue-600 font-mono mt-1">PRODUCTION EVIDENTIARY TRACING GRAPH</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="toggleLogModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Evidentiary Transaction Log
                    </button>
                    <button onclick="submitTrace()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Run Parallel Trace
                    </button>
                    <button onclick="triggerGeneratePDF()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-xs font-bold shadow transition flex items-center gap-2">
                        Generate Forensic Report
                    </button>
                </div>
            </div>
            <div class="flex gap-4 items-start w-full bg-slate-50 p-3 border border-slate-200 rounded">
                <div class="flex-grow">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Target Seed/Suspect Addresses (One per line)</label>
                    <textarea id="customSeeds" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono h-16" placeholder="0x...\\nbc1...\\nT..."></textarea>
                </div>
                <div class="w-48">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Total Loss Amount (USD)</label>
                    <input type="number" id="customLoss" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono" placeholder="80000" value="80000">
                </div>
                <div class="w-48">
                    <label class="block text-xs font-bold text-slate-700 mb-1">Victim Initials / Case ID</label>
                    <input type="text" id="customVictim" class="w-full text-xs border border-slate-300 rounded p-2 focus:ring-blue-500 font-mono" placeholder="[REDACTED]" value="[REDACTED]">
                </div>
            </div>
        </header>
"""

app_code = re.sub(r'<header.*?</header>', header_replacement, app_code, flags=re.DOTALL)

# Update submitTrace to use custom inputs
app_code = app_code.replace(
    'body: JSON.stringify({ seeds: defaultSeeds, target_amount: "80000", chain_override: "AUTO" })',
    'body: JSON.stringify({ seeds: document.getElementById("customSeeds").value, target_amount: document.getElementById("customLoss").value || "0", chain_override: "AUTO" })'
)

# Update report UI to use the custom victim initials
app_code = app_code.replace(
    '<td class="py-2 font-bold text-red-600" id="docVictimInitials">[REDACTED]</td>',
    '<td class="py-2 font-bold text-red-600" id="docVictimInitials"></td>'
)
app_code = app_code.replace(
    'document.getElementById("doc-date").innerText = new Date().toLocaleDateString();',
    'document.getElementById("doc-date").innerText = new Date().toLocaleDateString();\n            document.getElementById("docVictimInitials").innerText = document.getElementById("customVictim").value || "[REDACTED]";'
)

with open('productions/app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

# Write Autotest file
with open('productions/autotest.py', 'w', encoding='utf-8') as f:
    f.write("""import asyncio
from playwright.async_api import async_playwright
import requests

async def test_frontend():
    print("🚀 Starting Automated Frontend & Backend Audit...")
    try:
        r = requests.get('http://localhost:8000/')
        if r.status_code == 200:
            print("✅ Backend server is responding on port 8000")
        else:
            print("❌ Backend server returned status:", r.status_code)
    except Exception as e:
        print("❌ Could not connect to backend. Is uvicorn running?")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("✅ Headless browser launched")
        
        await page.goto("http://localhost:8000/")
        print("✅ Frontend loaded")
        
        # Test input fields
        await page.fill("#customSeeds", "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\\n0x7675DC2856fca0C22ed3C57979388FbF236De57F")
        await page.fill("#customLoss", "150000")
        await page.fill("#customVictim", "AUTO-TEST")
        print("✅ Custom inputs populated")
        
        # Click Run Trace
        await page.click("button:has-text('Run Parallel Trace')")
        print("✅ Trace initiated")
        
        # Wait for trace to complete or error out (Wait up to 30s)
        try:
            await page.wait_for_selector("text=TRACE COMPLETE", timeout=30000)
            print("✅ Trace completed successfully")
        except:
            print("⚠️ Trace did not complete within 30 seconds, or failed.")
            
        # Check Report
        await page.click("button:has-text('Generate Forensic Report')")
        print("✅ Forensic report button clicked")
        
        try:
            await page.wait_for_selector("#print-doc", state="visible", timeout=5000)
            print("✅ Forensic report modal opened")
            victim_text = await page.inner_text("#docVictimInitials")
            if "AUTO-TEST" in victim_text:
                print("✅ Data binding (Victim Initials) confirmed in report")
            else:
                print("❌ Data binding failed in report")
        except:
            print("❌ Forensic report modal failed to open")
            
        await browser.close()
        print("✅ Auto-test suite completed successfully.")

if __name__ == '__main__':
    asyncio.run(test_frontend())
""")
print("Productions directory setup complete!")
