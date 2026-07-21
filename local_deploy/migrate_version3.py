import os
import shutil
import re

mock_dir = r"C:\Users\LEGIONX\Downloads\nemesis\tracer_scripts\Advanced_Mock_Simulations\Enterprise_Starry_Flow_Mocks"
frontend_dir = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend"

print("Starting redesign migration...")

# 1. Copy all HTML files and assets
if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir)

# Copy Assets
assets_src = os.path.join(mock_dir, "assets")
assets_dst = os.path.join(frontend_dir, "assets")
if os.path.exists(assets_src):
    if not os.path.exists(assets_dst):
        shutil.copytree(assets_src, assets_dst)
        print(f"Copied assets to {assets_dst}")
    else:
        # copy contents
        for item in os.listdir(assets_src):
            s = os.path.join(assets_src, item)
            d = os.path.join(assets_dst, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        print("Updated assets folder.")

# Copy HTML files
html_files = ["index.html", "nemesis_id.html", "nemesis_tracer.html", "nemesis_intelligence.html", "recovery_framework.html", "intro.html"]
for file in html_files:
    src = os.path.join(mock_dir, file)
    dst = os.path.join(frontend_dir, file)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {file}")

# 2. Inject backend logic into nemesis_id.html
nemesis_id_path = os.path.join(frontend_dir, "nemesis_id.html")
if os.path.exists(nemesis_id_path):
    with open(nemesis_id_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The mock uses 'startDataFetch()' for the search button, let's replace it with 'executeSearch()' which is what our backend logic uses
    content = content.replace('onclick="startDataFetch()"', 'onclick="executeSearch()"')

    # Add the API integration script right before </body>
    api_script = """
    <script>
        // API Integration Logic injected by migration script
        async function executeSearch() {
            const input = document.getElementById('wallet-address');
            if(!input) return;
            const address = input.value.trim();
            if(!address) {
                alert("Please enter a target wallet address.");
                return;
            }

            // Show loader if available
            const loader = document.getElementById('loader-overlay');
            if(loader) loader.style.opacity = '1';

            try {
                // Fetch Data concurrently from Backend
                // Depending on APP_MODE this will go to /api or localhost:8088
                const backendUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8088' : '';
                
                const [walletRes, osintRes, geoRes, aiRes] = await Promise.all([
                    fetch(`${backendUrl}/api/wallet_profile/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/osint/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/nemesis_id/georisk/${address}`).catch(() => null),
                    fetch(`${backendUrl}/api/nemesis_id/ai_insights/${address}`).catch(() => null)
                ]);

                // Parse Data
                const walletData = walletRes ? await walletRes.json() : {};
                const osintData = osintRes ? await osintRes.json() : {};
                const geoData = geoRes ? await geoRes.json() : {};
                const aiData = aiRes ? await aiRes.json() : {};

                console.log("Wallet Data:", walletData);
                console.log("OSINT Data:", osintData);

                // Now flip the card
                const flipContainer = document.getElementById('flip-container');
                if(flipContainer) flipContainer.classList.add('flipped');
                
                const displayWallet = document.getElementById('display-wallet');
                if(displayWallet) displayWallet.innerText = address;
                
                // Populate Profile
                if(document.getElementById('prof-in')) document.getElementById('prof-in').textContent = `$${(walletData.usd_value || 0).toLocaleString()}`;
                
                // You can add more DOM manipulations here as needed based on the mock's DOM IDs
                
            } catch(e) {
                console.error("Fetch error:", e);
                alert("Failed to connect to NEMESIS Backend API.");
            } finally {
                if(loader) loader.style.opacity = '0';
            }
        }
    </script>
    """
    
    if "executeSearch()" not in content:
        content = content.replace("</body>", f"{api_script}\n</body>")
        with open(nemesis_id_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Injected backend API logic into nemesis_id.html")

print("Migration completed successfully.")
