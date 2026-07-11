import re
import os

html_path = r"c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\templates\nemesis_id_new.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove all via.placeholder.com logic
content = re.sub(r'onerror="this\.src=\'https://via\.placeholder\.com/[^\']+\'"', "", content)

# 2. Replace background-image: url('logo_nemesis.png') and <img src="logo_nemesis.png">
content = content.replace("url('logo_nemesis.png')", "none")
content = content.replace('src="logo_nemesis.png"', 'src="/static/images/logo_nemesis.png"')
content = content.replace('alt="LIONSGATE"', 'alt="LIONSGATE NETWORK"')

# 3. Clean up the tailwind CDN warning. 
tailwind_suppress = """
    <script>
        // Suppress Tailwind CDN production warning
        const originalWarn = console.warn;
        console.warn = function(...args) {
            if (args[0] && typeof args[0] === 'string' && args[0].includes('cdn.tailwindcss.com should not be used in production')) return;
            originalWarn.apply(console, args);
        };
    </script>
"""
if "cdn.tailwindcss.com" in content and "Suppress Tailwind" not in content:
    content = content.replace('<script src="https://cdn.tailwindcss.com"></script>', tailwind_suppress + '\n    <script src="https://cdn.tailwindcss.com"></script>')

# 4. Wipe hardcoded table data and add IDs to tbodys so we can populate them
# To safely wipe tbodys without breaking the HTML structure too much:
def tbody_replacer(match):
    # Give it an ID if it doesn't have one, or just add a general class
    return '<tbody class="dynamic-data-tbody">\n<!-- MOCK DATA STRIPPED - WAITING FOR API FETCH -->\n<tr><td colspan="6" class="text-center py-4 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Fetching Live Data...</td></tr>\n</tbody>'

content = re.sub(r'<tbody>.*?</tbody>', tbody_replacer, content, flags=re.DOTALL)

# 5. Inject fetch logic at the bottom of the body
fetch_script = """
    <script>
        // Dynamic Fetch Logic
        async function fetchNemesisIdData() {
            const urlParams = new URLSearchParams(window.location.search);
            const address = urlParams.get('address');
            if (!address) return;

            try {
                // 1. Fetch Profile
                const profileRes = await fetch(`/api/nemesis_id/profile/${address}`);
                if (profileRes.ok) {
                    const profileData = await profileRes.json();
                    
                    // Update header
                    const elHeaderAddr = document.getElementById('header-address');
                    if (elHeaderAddr) elHeaderAddr.innerText = profileData.address || address;
                    
                    // Update basic profile fields
                    document.getElementById('profile-nemesis-id') && (document.getElementById('profile-nemesis-id').innerText = profileData.nemesis_id || 'N/A');
                    document.getElementById('profile-entity-name') && (document.getElementById('profile-entity-name').innerText = profileData.entity_name || 'Unknown');
                    document.getElementById('profile-risk-score') && (document.getElementById('profile-risk-score').innerText = profileData.risk_score || '0');
                    document.getElementById('profile-balance') && (document.getElementById('profile-balance').innerText = `$${(profileData.estimated_balance_usd || 0).toLocaleString()}`);
                }

                // 2. Fetch AML
                const amlRes = await fetch(`/api/nemesis_id/aml/${address}`);
                if (amlRes.ok) {
                    const amlData = await amlRes.json();
                    document.getElementById('aml-score') && (document.getElementById('aml-score').innerText = amlData.risk_score || '0');
                    document.getElementById('aml-classification') && (document.getElementById('aml-classification').innerText = amlData.classification || 'Unknown');
                }

                // 3. Fetch TX History
                const txRes = await fetch(`/api/nemesis_id/tx_history/${address}`);
                if (txRes.ok) {
                    const txData = await txRes.json();
                    // Clear all tbodys that we marked
                    document.querySelectorAll('.dynamic-data-tbody').forEach(tbody => {
                        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-slate-400">Live data loaded successfully (See JS console for raw data). UI binding in progress.</td></tr>';
                    });
                    console.log("Loaded TX History:", txData);
                }

            } catch (err) {
                console.error("Error fetching NEMESIS ID data:", err);
            }
        }
        
        // Trigger fetch on load
        document.addEventListener('DOMContentLoaded', () => {
            fetchNemesisIdData();
        });
    </script>
"""

if "fetchNemesisIdData" not in content:
    content = content.replace("</body>", fetch_script + "\n</body>")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)
print("SUCCESS: Mock data stripped and dynamic fetch script injected.")
