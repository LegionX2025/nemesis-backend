import glob
import os

files = [
    r'C:\Users\LEGIONX\Downloads\cases\nemesis_project\cf_pages_build\nemesis_id.html',
    r'C:\Users\LEGIONX\Downloads\cases\nemesis_project\templates\nemesis_id.html'
]

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Update Header Tags
        html = html.replace(
            '<span class="text-slate-500 uppercase text-[10px] tracking-widest font-bold">NEMESIS ID: NMS-WALLET-ETH-00093231 | SUBJECT WALLET ENTITY</span>',
            '<span id="header-wallet-entity" class="text-slate-500 uppercase text-[10px] tracking-widest font-bold">NEMESIS ID: SCANNING... | SUBJECT WALLET ENTITY</span>'
        )

        html = html.replace(
            '''<div class="flex flex-wrap gap-2 mt-2 text-[9px] font-bold uppercase tracking-wider font-mono">
                        <span class="bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded shadow-sm cursor-pointer hover:bg-red-100 transition" onclick="openDossier('geo', 'Sanction Match')">HIGH RISK / LAZARUS LINKED</span>
                        <span class="bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded shadow-sm">CORPORATE SHELL</span>
                        <span class="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded shadow-sm">LAYER 4: OBFUSCATION DETECTED</span>
                        <div class="flex items-center gap-1.5 text-emerald-600 ml-2">
                            <span class="live-dot"></span> STATUS: ACTIVE
                        </div>
                    </div>''',
            '''<div id="header-tags-container" class="flex flex-wrap gap-2 mt-2 text-[9px] font-bold uppercase tracking-wider font-mono">
                        <!-- Dynamic tags will be populated here -->
                    </div>'''
        )

        html = html.replace(
            '''<div class="alert-flashing px-5 py-2.5 rounded-lg flex items-center gap-3 w-full md:w-auto shadow-sm cursor-pointer hover:bg-red-50 transition" onclick="openDossier('alert', 'CEX_EXPOSURE')">
                    <i class="fa-solid fa-building-columns text-2xl"></i>
                    <div>
                        <p class="text-[9px] font-black uppercase tracking-widest mb-0.5 font-mono">CEX / CUSTODIAL ALERT</p>
                        <p class="text-xs font-black tracking-tight">BINANCE HOT WALLET 14</p>
                    </div>
                </div>''',
            '''<div id="header-alert-box" class="hidden alert-flashing px-5 py-2.5 rounded-lg flex items-center gap-3 w-full md:w-auto shadow-sm cursor-pointer hover:bg-red-50 transition" onclick="openDossier('alert', 'CEX_EXPOSURE')">
                    <i class="fa-solid fa-building-columns text-2xl"></i>
                    <div>
                        <p class="text-[9px] font-black uppercase tracking-widest mb-0.5 font-mono">CEX / CUSTODIAL ALERT</p>
                        <p id="header-alert-text" class="text-xs font-black tracking-tight"></p>
                    </div>
                </div>'''
        )

        # 2. Executive Identity Reconstruction
        html = html.replace(
            '''<p class="text-sm text-slate-700 font-serif leading-relaxed mb-6 text-justify">
                        <strong>Summary:</strong> Using Advanced NLP LLM analytics, this wallet functions as a primary Tier-2 consolidation node explicitly tied to state-sponsored operations (APT38). It exhibits high-velocity, automated laundering patterns bridging EVM and non-EVM networks, evading sanctions before executing CEX/Custodial deposits.
                    </p>''',
            '''<p id="exec-summary" class="text-sm text-slate-700 font-serif leading-relaxed mb-6 text-justify">
                        <strong>Summary:</strong> Waiting for NLP LLM analytics...
                    </p>'''
        )

        html = html.replace(
            '<span class="text-slate-900 font-bold text-xs block">EOA / Smart Contract</span>',
            '<span id="wallet-type" class="text-slate-900 font-bold text-xs block">Scanning...</span>'
        )
        html = html.replace(
            '<span class="text-red-600 font-bold text-xs block">Mixer / Exchange Exposed</span>',
            '<span id="wallet-classification" class="text-red-600 font-bold text-xs block">Scanning...</span>'
        )
        html = html.replace(
            '<span class="text-slate-900 font-bold text-xs block">lazarus-proxy.eth</span>',
            '<span id="wallet-ens" class="text-slate-900 font-bold text-xs block">N/A</span>'
        )
        html = html.replace(
            '<span class="bg-red-600 text-white px-2 py-0.5 rounded inline-block mt-1">YES</span>',
            '<span id="wallet-malicious" class="bg-slate-300 text-slate-600 px-2 py-0.5 rounded inline-block mt-1">UNKNOWN</span>'
        )

        # Chronological Fund Flow
        html = html.replace(
            '''<h3 class="font-mono text-xs font-bold text-slate-600 uppercase mb-3">Chronological Fund Flow (Advanced Asset Lifecycle)</h3>
                    <div class="flex flex-col md:flex-row items-center justify-between gap-4 font-mono text-[10px]">
                        <div class="flip-card cursor-pointer" onclick="openDossier('intel', 'INGRESS')">
                            <div class="flip-card-inner">
                                <div class="flip-card-front bg-emerald-50/90 border-emerald-200">
                                    <span class="bg-emerald-600 text-white px-2 py-0.5 rounded text-[8px] mb-2 font-bold">INBOUND</span>
                                    <i class="fa-solid fa-mask text-2xl text-emerald-700 mb-1"></i>
                                    <span class="font-bold text-emerald-900">Tornado Cash Router</span>
                                </div>
                                <div class="flip-card-back">
                                    <strong class="text-blue-600 text-xs block mb-1">Obfuscation Entry</strong>
                                    <span>Type: Internal</span>
                                    <span>100 ETH deposited to break tracing heuristics.</span>
                                </div>
                            </div>
                        </div>
                        <i class="fa-solid fa-arrow-right-long text-blue-400 text-2xl animate-pulse"></i>
                        
                        <div class="flip-card cursor-pointer" onclick="openDossier('intel', 'SUBJECT')">
                            <div class="flip-card-inner">
                                <div class="flip-card-front bg-blue-50/90 border-blue-200">
                                    <span class="bg-blue-600 text-white px-2 py-0.5 rounded text-[8px] mb-2 font-bold">SUBJECT WALLET</span>
                                    <i class="fa-solid fa-wallet text-2xl text-blue-700 mb-1"></i>
                                    <span class="font-bold text-blue-900">0x742d...44e (ETH)</span>
                                </div>
                                <div class="flip-card-back">
                                    <strong class="text-blue-600 text-xs block mb-1">Consolidation</strong>
                                    <span>Type: Normal</span>
                                    <span>Automated programmatic aggregation of mixer funds.</span>
                                </div>
                            </div>
                        </div>
                        <i class="fa-solid fa-arrow-right-long text-red-400 text-2xl animate-pulse"></i>
                        
                        <div class="flip-card cursor-pointer" onclick="openDossier('intel', 'EGRESS')">
                            <div class="flip-card-inner">
                                <div class="flip-card-front bg-red-50/90 border-red-200">
                                    <span class="bg-red-600 text-white px-2 py-0.5 rounded text-[8px] mb-2 font-bold">OUTBOUND</span>
                                    <i class="fa-solid fa-building-columns text-2xl text-red-700 mb-1"></i>
                                    <span class="font-bold text-red-900">Binance Hot 14</span>
                                </div>
                                <div class="flip-card-back">
                                    <strong class="text-red-600 text-xs block mb-1">Terminal CEX</strong>
                                    <span>Type: Token Transfer</span>
                                    <span>Depositing funds into KYC exchange for fiat off-ramp.</span>
                                </div>
                            </div>
                        </div>
                    </div>''',
            '''<h3 class="font-mono text-xs font-bold text-slate-600 uppercase mb-3">Chronological Fund Flow (Advanced Asset Lifecycle)</h3>
                    <div id="fund-flow-container" class="flex flex-col md:flex-row items-center justify-between gap-4 font-mono text-[10px]">
                        <!-- Dynamic fund flow cards go here -->
                        <div class="text-slate-400 italic py-4 text-center w-full">Awaiting Trace Graph Generation...</div>
                    </div>'''
        )

        # 3. Profile Metadata
        html = html.replace('<span class="text-slate-900 font-bold">2023-04-12 14:02 UTC</span>', '<span id="first-activity" class="text-slate-900 font-bold">N/A</span>')
        html = html.replace('<span class="text-slate-900 font-bold">2026-05-27 08:14 UTC</span>', '<span id="last-activity" class="text-slate-900 font-bold">N/A</span>')
        html = html.replace('<span id="tx-count" class="text-slate-900 font-black">14,205</span>', '<span id="tx-count" class="text-slate-900 font-black">0</span>')
        html = html.replace('<span class="text-emerald-600 font-bold usd-value">$84,500,000</span><span class="text-emerald-600 font-bold native-value">26,500 ETH</span>', '<span id="total-inbound-usd" class="text-emerald-600 font-bold usd-value">$0.00</span><span id="total-inbound-native" class="text-emerald-600 font-bold native-value">0.00</span>')
        html = html.replace('<span class="text-red-600 font-bold usd-value">$83,047,109</span><span class="text-red-600 font-bold native-value">26,047 ETH</span>', '<span id="total-outbound-usd" class="text-red-600 font-bold usd-value">$0.00</span><span id="total-outbound-native" class="text-red-600 font-bold native-value">0.00</span>')
        html = html.replace('<span id="total-asset-value" class="text-blue-600 font-bold usd-value">$1,452,890</span><span class="text-blue-600 font-bold native-value">453 ETH</span>', '<span id="total-asset-value" class="text-blue-600 font-bold usd-value">$0.00</span><span id="total-asset-native" class="text-blue-600 font-bold native-value">0.00</span>')
        html = html.replace('''<span class="text-purple-600 font-bold cursor-pointer hover:underline" onclick="openDossier('wallet', '0xd90e...31b')">0xd90e...31b (Mixer)</span><br>
                                <span class="text-[8px]">TX: 0xab8f...9c1a</span>''', '<span id="funded-by" class="text-purple-600 font-bold">N/A</span>')

        # 4. Interacted With & Clustered Wallets
        html = html.replace('''<tbody class="font-mono text-xs">
                            <tr class="cursor-pointer" onclick="openDossier('wallet', '0x28c...d60')">
                                <td class="text-blue-600 hover:underline font-bold">0x28c6c06298d514db089934071355e5743bf21d60</td>
                                <td><span class="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[9px] font-bold border border-amber-200">CUSTODIAL (Binance)</span></td>
                                <td class="text-center text-red-600 font-black"><i class="fa-solid fa-arrow-up"></i> OUTBOUND</td>
                                <td class="text-right font-black text-slate-900"><span class="val-usd">$1,200,000</span><span class="val-native">400 ETH</span></td>
                                <td><img src="https://cryptologos.cc/logos/ethereum-eth-logo.png" class="w-4 h-4 inline" onerror="this.style.display='none'"> ETH</td>
                            </tr>
                            <tr class="cursor-pointer" onclick="openDossier('wallet', '0xd90...31b')">
                                <td class="text-blue-600 hover:underline font-bold">0xd90e2f925da726b50c4ed8d0fb90ad053324f31b</td>
                                <td><span class="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-[9px] font-bold border border-purple-200">MIXER (Tornado Cash)</span></td>
                                <td class="text-center text-emerald-600 font-black"><i class="fa-solid fa-arrow-down"></i> INBOUND</td>
                                <td class="text-right font-black text-slate-900"><span class="val-usd">$10,000,000</span><span class="val-native">3,125 ETH</span></td>
                                <td><img src="https://cryptologos.cc/logos/ethereum-eth-logo.png" class="w-4 h-4 inline" onerror="this.style.display='none'"> ETH</td>
                            </tr>
                        </tbody>''', '<tbody id="interacted-with-body" class="font-mono text-xs"></tbody>')

        # 5. Counterparties
        html = html.replace('<p class="font-mono text-3xl font-black text-emerald-600 val-usd">$84,500,000</p>', '<p id="counterparty-in-usd" class="font-mono text-3xl font-black text-emerald-600 val-usd">$0.00</p>')
        html = html.replace('<p class="font-mono text-3xl font-black text-emerald-600 val-native">26,500 ETH</p>', '<p id="counterparty-in-native" class="font-mono text-3xl font-black text-emerald-600 val-native">0.00</p>')
        html = html.replace('<p class="font-mono text-3xl font-black text-red-600 val-usd">$83,047,109</p>', '<p id="counterparty-out-usd" class="font-mono text-3xl font-black text-red-600 val-usd">$0.00</p>')
        html = html.replace('<p class="font-mono text-3xl font-black text-red-600 val-native">26,047 ETH</p>', '<p id="counterparty-out-native" class="font-mono text-3xl font-black text-red-600 val-native">0.00</p>')

        html = html.replace('''<tbody class="font-mono text-xs">
                            <tr class="cursor-pointer hover:bg-slate-50 transition" onclick="openDossier('intel', 'Counterparty Profile')">
                                <td class="text-slate-500">2026-05-27 08:14</td>
                                <td><img src="https://cryptologos.cc/logos/ethereum-eth-logo.png" class="w-4 h-4 inline" onerror="this.style.display='none'"> ETH</td>
                                <td class="text-blue-600">0xab12...89ef</td>
                                <td><span class="font-bold text-slate-800">CLS-88921 (Binance Hot)</span></td>
                                <td class="text-slate-600">0x28c...d60</td>
                                <td class="text-slate-500 text-[10px]">CEX Custodial Cashout endpoint.</td>
                            </tr>
                        </tbody>''', '<tbody id="counterparties-body" class="font-mono text-xs"></tbody>')

        # 6. Transactions
        html = html.replace('''<span class="font-mono text-lg font-black text-emerald-600">IN: <span class="val-usd">$84.5M</span><span class="val-native">26.5k ETH</span></span>
                            <span class="font-mono text-lg font-black text-red-600">OUT: <span class="val-usd">$83.0M</span><span class="val-native">26.0k ETH</span></span>''', '''<span class="font-mono text-lg font-black text-emerald-600">IN: <span id="tx-in-usd" class="val-usd">$0.00</span><span id="tx-in-native" class="val-native">0.00</span></span>
                            <span class="font-mono text-lg font-black text-red-600">OUT: <span id="tx-out-usd" class="val-usd">$0.00</span><span id="tx-out-native" class="val-native">0.00</span></span>''')

        html = html.replace('''<tbody class="font-mono text-xs">
                            <tr class="cursor-pointer hover:bg-blue-50 transition" onclick="openDossier('tx', '0xab12...89ef')">
                                <td class="text-slate-600">2026-05-27 08:14</td>
                                <td><img src="https://cryptologos.cc/logos/ethereum-eth-logo.png" class="w-4 h-4 inline mr-1" onerror="this.style.display='none'"> ETH</td>
                                <td class="text-blue-600 hover:underline" onclick="event.stopPropagation(); verifyOnExplorer('0xab12...89ef')">0xab12...89ef</td>
                                <td><span class="bg-amber-100 text-amber-800 border border-amber-300 px-1.5 py-0.5 rounded text-[9px] font-bold">CEX_DEPOSIT</span></td>
                                <td class="text-center text-red-600 font-black"><i class="fa-solid fa-arrow-right"></i> OUT</td>
                                <td><span class="text-slate-900 font-bold">SUBJECT (EOA)</span></td>
                                <td><span class="text-amber-700 font-bold">Binance Hot 14</span></td>
                                <td class="text-right font-black text-slate-900"><span class="val-usd text-red-600">-$1,200,000</span><span class="val-native text-red-600">-400 ETH</span></td>
                                <td class="text-[9px] text-slate-500">Terminal Egress / Cash Out</td>
                            </tr>
                        </tbody>''', '<tbody id="transactions-body" class="font-mono text-xs"></tbody>')

        # 7. AML
        html = html.replace('<div class="text-7xl font-black font-mono text-red-600 drop-shadow-sm">94<span class="text-3xl text-red-400">.2</span></div>', '<div id="aml-score-display" class="text-7xl font-black font-mono text-red-600 drop-shadow-sm">0<span class="text-3xl text-red-400">.0</span></div>')
        html = html.replace('<div class="text-xs font-bold uppercase tracking-widest text-red-700 mt-2">Critical AML Risk</div>', '<div id="aml-risk-level" class="text-xs font-bold uppercase tracking-widest text-red-700 mt-2">Analyzing...</div>')
        html = html.replace('''<div class="space-y-3 font-mono text-[10px]">
                            <div class="flex justify-between items-center"><span class="text-slate-600">Exposure Rate</span><span class="text-red-600 font-bold bg-red-50 px-2 py-0.5 rounded border border-red-200">94.2%</span></div>
                            <div class="flex justify-between items-center"><span class="text-slate-600">Sanctions Overlap (OFAC)</span><span class="text-red-600 font-bold">Critical (35%)</span></div>
                            <div class="flex justify-between items-center"><span class="text-slate-600">Mixer Exposure</span><span class="text-red-600 font-bold">High (20%)</span></div>
                        </div>''', '<div id="aml-flags-container" class="space-y-3 font-mono text-[10px]"></div>')

        # 8. GeoRisk
        html = html.replace('''<div class="hidden group-hover:block bg-white border border-red-200 text-[10px] font-mono p-3 rounded mt-2 absolute top-2 w-64 z-30 shadow-xl">
                            <strong class="text-red-700 block mb-1 text-xs">Primary Operations: DPRK</strong>
                            <span class="text-slate-600">IP: <span class="text-slate-900 font-bold">175.45.176.x</span></span>
                        </div>''', '''<div id="georisk-hover" class="hidden group-hover:block bg-white border border-red-200 text-[10px] font-mono p-3 rounded mt-2 absolute top-2 w-64 z-30 shadow-xl">
                            <strong id="georisk-location" class="text-red-700 block mb-1 text-xs">Awaiting Trace Details...</strong>
                        </div>''')

        # 9. Intelligence
        html = html.replace('''<div class="bg-amber-50 border border-amber-200 p-4 rounded mb-6 font-mono text-xs text-amber-900 shadow-sm">
                    <strong>Custodial Wallet Entry:</strong> Binance Deposit Address 0x28c6c06298d514db089934071355e5743bf21d60
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs">
                    <div class="bg-white p-4 rounded border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 transition" onclick="openDossier('intel', 'Telegram Signal')">
                        <span class="text-slate-500 font-bold block mb-1">Social Media</span>
                        <span class="text-blue-600 font-bold block">Telegram: @laundromat_rx</span>
                    </div>
                    <div class="bg-white p-4 rounded border border-slate-200 shadow-sm cursor-pointer hover:border-red-400 transition" onclick="openDossier('intel', 'Darknet Signal')">
                        <span class="text-slate-500 font-bold block mb-1">Darknet</span>
                        <span class="text-red-600 font-bold block">XSS.is / Exploit.in</span>
                    </div>
                </div>''', '<div id="intelligence-content"></div>')

        # 10. AI Insights
        html = html.replace('''<p><strong>Summary:</strong> The "discontinuity problem" represents the holy grail of modern crypto forensics. When an asset moves from Ethereum, enters a decentralized bridge or a mixer, and emerges on Solana, the native ledger link is physically and cryptographically severed.</p>''', '<p id="ai-insights-text">Awaiting trace analysis to generate insights...</p>')

        # 11. Report Date and ID
        html = html.replace('NEMESIS ID: <span style="font-weight: bold;">NMS-WALLET-ETH-00093231</span> | DATE: May 27, 2026', 'NEMESIS ID: <span id="report-id" style="font-weight: bold;">PENDING</span> | DATE: <span id="report-date"></span>')
        html = html.replace('Terminal Custodial Entity Identified: <strong>Binance Hot Wallet 14</strong>', 'Terminal Custodial Entity Identified: <strong id="report-terminal">Pending Analysis</strong>')
        html = html.replace('''Lionsgate Network's NEMESIS engine has successfully mapped the omni-chain flow of assets. The deterministic algorithm resolved the terminal destination of funds to a KYC-regulated Centralized Exchange (CEX).''', '''Lionsgate Network's NEMESIS engine will map the omni-chain flow of assets. Run a scan to populate the report.''')

        # 12. Javascript Logic Replacement
        js_replace = '''
        // NEMESIS ID: Live Fetch Logic
        async function executeNemesisSearch() {
            const inputEl = document.getElementById('nemesis-search-input');
            const target = inputEl.value.trim();
            if (!target) return;
            
            // Set UI header
            document.getElementById('active-wallet-id').innerHTML = `${target} <i class="fa-solid fa-copy text-[10px] text-slate-400"></i>`;
            
            triggerLoader("Querying NEMESIS Omega Framework...");
            
            try {
                // We do a Promise.all to fetch profile, aml, intel, and tx history concurrently
                const [profileRes, amlRes, intelRes, txRes] = await Promise.all([
                    fetch(`https://nemesis-local.onrender.com/api/nemesis_id/profile/${target}`).catch(e => ({ok: false})),
                    fetch(`https://nemesis-local.onrender.com/api/nemesis_id/aml/${target}`).catch(e => ({ok: false})),
                    fetch(`https://nemesis-local.onrender.com/api/nemesis_id/intel/${target}`).catch(e => ({ok: false})),
                    fetch(`https://nemesis-local.onrender.com/api/nemesis_id/tx_history/${target}`).catch(e => ({ok: false}))
                ]);
                
                const profile = profileRes.ok ? await profileRes.json() : {};
                const aml = amlRes.ok ? await amlRes.json() : {};
                const intel = intelRes.ok ? await intelRes.json() : {};
                const txHistory = txRes.ok ? await txRes.json() : { transactions: [] };
                
                populateDynamicDossier(profile, aml, intel, txHistory);
                
                // Fire off the backend trace as well
                const formData = new FormData();
                formData.append('target_address', target);
                fetch('https://nemesis-local.onrender.com/trace', { method: 'POST', body: formData }).catch(e => console.log('Trace started in background'));
                
            } catch (err) {
                console.error("NEMESIS Fetch Error:", err);
                alert("Failed to connect to Omega Backend.");
            }
        }
        
        function populateDynamicDossier(profile, aml, intel, txHistory) {
            // Header Tags
            const tagsContainer = document.getElementById('header-tags-container');
            if (tagsContainer) {
                tagsContainer.innerHTML = '';
                if (aml.risk_level && aml.risk_level.includes('Critical')) {
                    tagsContainer.innerHTML += `<span class="bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded shadow-sm">HIGH RISK / CRITICAL</span>`;
                }
                if (profile.entity && profile.entity !== 'Unknown Entity') {
                    tagsContainer.innerHTML += `<span class="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-0.5 rounded shadow-sm">${profile.entity.toUpperCase()}</span>`;
                }
                tagsContainer.innerHTML += `<div class="flex items-center gap-1.5 text-emerald-600 ml-2"><span class="live-dot"></span> STATUS: ACTIVE</div>`;
            }
            
            // Profile & Balances
            if (profile.balance) {
                document.getElementById('total-asset-value').innerText = profile.balance;
                document.getElementById('total-inbound-usd').innerText = profile.total_received || "$0.00";
                document.getElementById('total-outbound-usd').innerText = profile.total_sent || "$0.00";
                
                document.getElementById('counterparty-in-usd').innerText = profile.total_received || "$0.00";
                document.getElementById('counterparty-out-usd').innerText = profile.total_sent || "$0.00";
                document.getElementById('tx-in-usd').innerText = profile.total_received || "$0.00";
                document.getElementById('tx-out-usd').innerText = profile.total_sent || "$0.00";
            }
            if (profile.tx_count !== undefined) {
                document.getElementById('tx-count').innerText = profile.tx_count;
            }
            if (profile.first_activity) {
                document.getElementById('first-activity').innerText = profile.first_activity;
                document.getElementById('last-activity').innerText = profile.last_activity || "N/A";
            }
            
            // AML Score
            if (aml.risk_score !== undefined) {
                const scoreDisplay = document.getElementById('aml-score-display');
                if (scoreDisplay) {
                    const whole = Math.floor(aml.risk_score);
                    const decimal = (aml.risk_score % 1).toFixed(1).substring(1); // gets ".X"
                    scoreDisplay.innerHTML = `${whole}<span class="text-3xl text-red-400">${decimal}</span>`;
                }
                document.getElementById('aml-risk-level').innerText = aml.risk_level + " AML Risk";
                
                const amlFlags = document.getElementById('aml-flags-container');
                if (amlFlags) {
                    amlFlags.innerHTML = '';
                    if (aml.flags && aml.flags.length > 0) {
                        aml.flags.forEach(f => {
                            amlFlags.innerHTML += `<div class="flex justify-between items-center"><span class="text-slate-600">${f}</span><span class="text-red-600 font-bold">Detected</span></div>`;
                        });
                    } else {
                        amlFlags.innerHTML = `<div class="flex justify-between items-center"><span class="text-slate-600">Exposure Rate</span><span class="text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Minimal</span></div>`;
                    }
                }
            }
            
            // Intelligence
            const intelContainer = document.getElementById('intelligence-content');
            if (intelContainer && intel.intel_summary) {
                intelContainer.innerHTML = `<div class="bg-amber-50 border border-amber-200 p-4 rounded mb-6 font-mono text-xs text-amber-900 shadow-sm">
                    <strong>Intel Summary:</strong> ${intel.intel_summary}
                </div>`;
            }
            
            // Transactions Table
            const txBody = document.getElementById('transactions-body');
            if (txBody && txHistory.transactions) {
                txBody.innerHTML = '';
                txHistory.transactions.forEach(tx => {
                    const isOut = tx.from && tx.from.toLowerCase() === profile.address.toLowerCase();
                    const flowIcon = isOut ? '<i class="fa-solid fa-arrow-right"></i> OUT' : '<i class="fa-solid fa-arrow-left"></i> IN';
                    const flowColor = isOut ? 'text-red-600' : 'text-emerald-600';
                    const amount = tx.amount || "0";
                    txBody.innerHTML += `
                    <tr class="cursor-pointer hover:bg-slate-50 transition" onclick="openDossier('tx', '${tx.hash}')">
                        <td class="text-slate-600">${tx.timestamp || 'N/A'}</td>
                        <td>${tx.chain || 'AUTO'}</td>
                        <td class="text-blue-600 hover:underline">${tx.hash ? tx.hash.substring(0, 10) + '...' : 'N/A'}</td>
                        <td><span class="bg-slate-100 text-slate-800 border border-slate-300 px-1.5 py-0.5 rounded text-[9px] font-bold">TRANSFER</span></td>
                        <td class="text-center ${flowColor} font-black">${flowIcon}</td>
                        <td><span class="text-slate-900 font-bold">${tx.from ? tx.from.substring(0, 8) + '...' : 'Unknown'}</span></td>
                        <td><span class="text-slate-900 font-bold">${tx.to ? tx.to.substring(0, 8) + '...' : 'Unknown'}</span></td>
                        <td class="text-right font-black text-slate-900"><span class="val-usd ${flowColor}">${amount}</span></td>
                        <td class="text-[9px] text-slate-500">Processed Transfer</td>
                    </tr>
                    `;
                });
            }
        }
'''

        html = html.replace('''        // NEMESIS ID: Live Fetch Logic
        async function executeNemesisSearch() {
            const inputEl = document.getElementById('nemesis-search-input');
            const target = inputEl.value.trim();
            if (!target) return;
            
            // Set UI header
            document.getElementById('active-wallet-id').innerHTML = `${target} <i class="fa-solid fa-copy text-[10px] text-slate-400"></i>`;
            
            triggerLoader("Querying NEMESIS Omega Framework...");
            
            try {
                const formData = new FormData();
                formData.append('target_address', target);
                
                const res = await fetch('/trace', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await res.json();
                if(data.error) {
                    alert("Analysis Failed: " + data.error);
                    return;
                }
                
                // Populate DOM with Live Data
                populateDossier(data);
                
            } catch (err) {
                console.error("NEMESIS Fetch Error:", err);
                alert("Failed to connect to Omega Backend.");
            }
        }
        
        function populateDossier(data) {
            // Update Balance if node exists
            if (data.nodes && data.nodes.length > 0) {
                const primaryNode = data.nodes[0];
                const balanceEl = document.getElementById('total-asset-value');
                if(balanceEl && primaryNode.balance !== undefined) {
                    balanceEl.innerText = `$${parseFloat(primaryNode.balance).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
                }
            }
            
            // Update Activity
            const txCountEl = document.getElementById('tx-count');
            if (txCountEl && data.edges) {
                txCountEl.innerText = data.edges.length;
            }
        }''', js_replace)

        # Clear out nodes/edges from initTraceGraph
        html = html.replace('''const nodes = new vis.DataSet([
                { id: 1, label: 'SUBJECT EOA\\n0x742...', color: { background: '#ef4444', border: '#b91c1c' }, font: { color: '#ffffff' }, size: 30, level: 2 },
                { id: 2, label: 'Tornado Cash\\nMixer', color: { background: '#64748b', border: '#475569' }, font: { color: '#ffffff' }, size: 25, level: 1 },
                { id: 3, label: 'Stargate Router\\nBridge/Contract', color: { background: '#8b5cf6', border: '#6d28d9' }, font: { color: '#ffffff' }, size: 25, level: 3 },
                { id: 4, label: 'Binance Hot 14\\nCEX/Custodial', color: { background: '#f59e0b', border: '#d97706' }, font: { color: '#ffffff' }, size: 35, level: 4 }
            ]);

            const edges = new vis.DataSet([
                { id: 'e1', from: 2, to: 1, label: '🟢 100 ETH', font: { color: '#1e293b', align: 'horizontal', background: 'rgba(255,255,255,0.8)' }, width: 3, color: { color: '#ef4444' } },
                { id: 'e3', from: 1, to: 3, label: '🟣 5.5M USDC', font: { color: '#1e293b', align: 'horizontal', background: 'rgba(255,255,255,0.8)' }, width: 3, color: { color: '#8b5cf6' } },
                { id: 'e4', from: 1, to: 4, label: '🟠 400 ETH', font: { color: '#1e293b', align: 'horizontal', background: 'rgba(255,255,255,0.8)' }, width: 4, color: { color: '#f59e0b' } }
            ]);''', '''const nodes = new vis.DataSet([]);
            const edges = new vis.DataSet([]);''')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Failed {file_path}: {e}")
