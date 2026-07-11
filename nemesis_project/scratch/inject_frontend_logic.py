import re
import os

file_path = r"C:\Users\LEGIONX\downloads\cases\nemesis_project\templates\nemesis_id.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# The new executeNemesisID function
new_js = """
        async function executeNemesisID() {
            let address = document.getElementById('id-search-input').value.trim();
            if(!address) {
                alert("Please enter a wallet address");
                return;
            }
            
            triggerLoader("Reconstructing Profile & Gathering Intel...");
            
            try {
                const backendUrl = window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1') ? '' : 'https://nemesis-local.onrender.com';
                
                // Fetch all data streams concurrently
                const [profileRes, networkRes, tokensRes, chainsRes, txRes, balRes, riskRes, intelRes] = await Promise.allSettled([
                    fetch(`${backendUrl}/api/nemesis_id/profile/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/network/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/tokens/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/chains/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/transactions/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/balances/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/risk/${address}`).then(r => r.json()),
                    fetch(`${backendUrl}/api/nemesis_id/intelligence/${address}`).then(r => r.json())
                ]);

                document.getElementById('id-landing').classList.add('hidden');
                let dash = document.getElementById('id-dashboard');
                dash.classList.remove('hidden');
                dash.classList.add('flex');
                
                // --- Tab 1: Profile ---
                if (profileRes.status === "fulfilled") {
                    const p = profileRes.value;
                    let addrFields = document.querySelectorAll("h1.font-mono");
                    if(addrFields.length > 0) addrFields[0].innerHTML = (p.address || address) + ` <i class="fa-solid fa-copy text-xs text-slate-400"></i>`;
                    
                    if(document.getElementById("val-net-balance")) document.getElementById("val-net-balance").innerText = "$" + (p.total_balance_usd || 0).toLocaleString();
                    if(document.getElementById("val-first-activity")) document.getElementById("val-first-activity").innerText = (p.first_active || "N/A");
                    if(document.getElementById("val-last-activity")) document.getElementById("val-last-activity").innerText = (p.last_active || "N/A");
                }

                // --- Tab 5: Transactions ---
                if (txRes.status === "fulfilled") {
                    const txData = txRes.value;
                    const txBody = document.getElementById('tx-history-body');
                    if (txBody) {
                        txBody.innerHTML = '';
                        if (txData.transactions && txData.transactions.length > 0) {
                            txData.transactions.forEach(tx => {
                                let html = `<tr class="cursor-pointer hover:bg-blue-50 transition" onclick="verifyOnExplorer('${tx.hash}')">
                                    <td class="text-slate-600">${tx.timestamp || 'Unknown'}</td>
                                    <td><span class="bg-indigo-100 text-indigo-800 border border-indigo-300 px-1.5 py-0.5 rounded font-bold">${tx.method || 'TRANSFER'}</span></td>
                                    <td class="text-blue-600 hover:underline">${(tx.hash || '').substring(0,6)}...${(tx.hash || '').substring((tx.hash || '').length-4)}</td>
                                    <td class="font-bold text-slate-800">${(tx.from || '').substring(0,5)}...</td>
                                    <td class="font-bold text-slate-800">${(tx.to || '').substring(0,5)}...</td>
                                    <td class="text-amber-700 font-bold">Unknown</td>
                                    <td class="text-right font-black text-slate-900"><span class="val-usd text-red-600">${tx.value_eth || 0} ETH</span></td>
                                    <td><span class="bg-amber-100 text-amber-800 border border-amber-300 px-1.5 py-0.5 rounded font-bold">TRANSFERS</span></td>
                                    <td class="text-slate-700 font-bold">N/A</td>
                                    <td class="text-slate-600">N/A</td>
                                    <td><span class="text-emerald-600 font-black">90%</span></td>
                                    <td class="text-slate-600">N/A</td>
                                    <td class="text-slate-500 italic">Standard transfer</td>
                                </tr>`;
                                txBody.innerHTML += html;
                            });
                        }
                    }
                }

                // --- Tab 8 & 9: Risk & AML ---
                if (riskRes.status === "fulfilled") {
                    const r = riskRes.value;
                    const amlScore = document.getElementById('aml-score-display');
                    const amlRisk = document.getElementById('aml-risk-level');
                    if (amlScore) amlScore.innerHTML = `${r.aml.risk_score || 0}<span class="text-3xl text-red-400">.0</span>`;
                    if (amlRisk) amlRisk.innerText = r.aml.risk_level || "UNKNOWN";
                    
                    const flagsContainer = document.getElementById('aml-flags-container');
                    if (flagsContainer && r.aml.flags) {
                        flagsContainer.innerHTML = r.aml.flags.map(f => `<div class="flex items-center gap-2 text-red-700"><i class="fa-solid fa-triangle-exclamation"></i> ${f}</div>`).join('');
                    }

                    const geoLoc = document.getElementById('georisk-location');
                    if (geoLoc && r.georisk) {
                        geoLoc.innerHTML = `Primary Region: ${r.georisk.primary_region}<br>Activity Zones: ${r.georisk.activity_zones.join(', ')}`;
                    }
                }

                // --- Tab 11: AI Insights ---
                if (intelRes.status === "fulfilled") {
                    const intel = intelRes.value;
                    const aiText = document.getElementById('ai-insights-text');
                    if (aiText) {
                        aiText.innerHTML = `
                            <p><strong>Behavioral Insights:</strong> ${intel.ai_insights.insights}</p>
                            <p><strong>Psychological Profile:</strong> ${intel.ai_insights.psychological_profile}</p>
                            <p><strong>Anomalies:</strong> ${intel.ai_insights.behavioral_anomalies.join(', ')}</p>
                        `;
                    }
                }
                
            } catch (err) {
                console.error(err);
                alert("Failed to load dossier from backend. Network error.");
            }
        }
"""

# Extract everything before executeNemesisID
pattern = re.compile(r"async function executeNemesisID\(\) \{.*?(?=\s*// Init UI)", re.DOTALL)
if pattern.search(content):
    new_content = pattern.sub(new_js, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced executeNemesisID")
else:
    print("Could not find executeNemesisID pattern")
