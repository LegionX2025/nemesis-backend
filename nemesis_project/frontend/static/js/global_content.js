// ==============================================================================
// 🛡️ LIONSGATE INTELLIGENCE NETWORK - GLOBAL MODAL CONTENT ENGINE
// ==============================================================================

const contentData = {
    // ----------------------------------------------------------------------
    // 1. LEGAL & COMPLIANCE
    // ----------------------------------------------------------------------
    'license': {
        title: '<i class="fa-solid fa-scale-balanced mr-2"></i> Software License & IP',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <div class="bg-blue-50 p-5 border-l-4 border-blue-600 rounded">
                    <h3 class="font-bold text-blue-900 mb-1">RESTRICTED - AUTHORIZED USE ONLY</h3>
                    <p class="text-sm text-blue-800">NEMESIS Trace™, Nemesis ID™, OmniChain Engine™, and associated APIs are the exclusive intellectual property of Lionsgate Intelligence Network.</p>
                </div>
                
                <div>
                    <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mb-3">1. Intellectual Property & Ownership</h4>
                    <p class="text-sm">The NEMESIS platform, including but not limited to the NEMESIS Trace engine, Nemesis ID profiling system, underlying machine learning algorithms, Global Blockchain Intelligence Ontology (GBIO), and all associated source code, UI/UX designs, and documentation, are the exclusive intellectual property of Lionsgate Intelligence Network.</p>
                    <p class="text-sm mt-2">All rights, titles, and interests in and to the Software are protected by international copyright, trademark, and trade secret laws. The terms "NEMESIS", "Nemesis ID", and "Lionsgate Intelligence Network" are registered trademarks.</p>
                </div>

                <div>
                    <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mb-3">2. Grant of License</h4>
                    <p class="text-sm">Subject to the terms and conditions of this Agreement, Lionsgate Intelligence Network grants the Authorized Entity a revocable, non-exclusive, non-transferable, and non-sublicensable license to access and use the Software strictly for its internal cyber-investigative, compliance, auditing, and law enforcement purposes.</p>
                </div>

                <div>
                    <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mb-3">3. Strict Restrictions (The "Prohibited Acts")</h4>
                    <ul class="list-disc pl-5 space-y-2 text-sm">
                        <li><strong>Reverse Engineer:</strong> Decompile, disassemble, or reverse-engineer the Software, tracing engines, clustering algorithms, or data payloads.</li>
                        <li><strong>Scrape or Automate:</strong> Use unauthorized bots, spiders, or scrapers to extract data, topological graphs, or Threat Intelligence feeds from the Platform.</li>
                        <li><strong>Resell or Redistribute:</strong> Sub-license, rent, lease, or resell access to the Nemesis platform or its generated API outputs to unauthorized third parties.</li>
                        <li><strong>Compromise Integrity:</strong> Attempt to bypass rate limits, Edge proxy signatures, Cloudflare WebAssembly isolates, or tamper with the Chain of Custody hashes embedded in the evidentiary reports.</li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mb-3">4. Disclaimer of Warranties</h4>
                    <p class="text-sm">THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. LIONSGATE INTELLIGENCE NETWORK EXPLICITLY DISCLAIMS ALL WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.</p>
                    <p class="text-sm mt-2">While NEMESIS achieves up to 98% recovery probability mapping and highly accurate entity resolution, Lionsgate Intelligence Network does not guarantee the recovery of stolen assets. Only competent legal and law enforcement authorities possess the jurisdiction to freeze, seize, or subpoena assets held by custodial entities identified in NEMESIS reports.</p>
                </div>

                <div>
                    <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mb-3">5. Limitation of Liability</h4>
                    <p class="text-sm">In no event shall Lionsgate Intelligence Network be held liable for any indirect, incidental, special, or consequential damages—including loss of profits, data, or operational disruptions—arising from the use or inability to use the NEMESIS platform.</p>
                </div>
                
                <div class="text-xs text-slate-500 mt-8 text-center">
                    By authenticating into the NEMESIS platform, you acknowledge that you have read, understood, and agreed to be bound by these proprietary terms.
                </div>
            </div>
        `
    },
    'terms': {
        title: '<i class="fa-solid fa-file-contract mr-2"></i> Terms of Service',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <p class="text-sm italic">Effective Date: 2026</p>
                <p class="text-sm">Welcome to Lionsgate Network. By accessing our platform and utilizing our investigative tools, you agree to comply with and be bound by the following Terms of Service.</p>
                
                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">1. Use of Services</h4>
                <p class="text-sm">Our services are intended for legal compliance, asset recovery, and cyber-investigative purposes. You agree to use the services only for lawful purposes and in accordance with all applicable international laws and regulations.</p>

                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">2. Confidentiality</h4>
                <p class="text-sm">As an intelligence network, we handle highly sensitive data. You agree to maintain the strict confidentiality of any reports, intelligence, or platform outputs generated by NEMESIS or provided by our analysts.</p>

                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">3. User Accounts</h4>
                <p class="text-sm">You are responsible for maintaining the confidentiality of your account credentials. Any activity occurring under your account is your responsibility. Immediate notification is required upon discovery of any unauthorized use.</p>

                <div class="bg-slate-100 p-4 rounded text-xs text-center text-slate-500 mt-6">
                    For full legal terms, visit <a href="https://lionsgate.network/terms-conditions/" target="_blank" class="text-blue-600 hover:underline">lionsgate.network/terms-conditions</a>
                </div>
            </div>
        `
    },
    'privacy': {
        title: '<i class="fa-solid fa-shield-halved mr-2"></i> Privacy Policy',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <p class="text-sm">Lionsgate Network ("we", "our", or "us") is committed to protecting your privacy and ensuring the security of your data. This Privacy Policy outlines our practices regarding data collection and usage.</p>
                
                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">1. Information We Collect</h4>
                <p class="text-sm">We collect information that you provide directly to us, including account registration details, API query parameters, and operational telemetry required to secure the platform against unauthorized access.</p>

                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">2. How We Use Your Data</h4>
                <p class="text-sm">Your data is used exclusively to provision your access to the NEMESIS platform, process your intelligence queries, and maintain strict audit logs for compliance with law enforcement standards.</p>

                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2">3. Data Security</h4>
                <p class="text-sm">We implement military-grade encryption for data at rest and in transit. Access to production environments is strictly controlled via Zero-Trust architecture.</p>

                <div class="bg-slate-100 p-4 rounded text-xs text-center text-slate-500 mt-6">
                    For our complete Privacy Policy, visit <a href="https://lionsgate.network/privacy-policy-2/" target="_blank" class="text-blue-600 hover:underline">lionsgate.network/privacy-policy-2</a>
                </div>
            </div>
        `
    },

    // ----------------------------------------------------------------------
    // 2. CORPORATE & HISTORY
    // ----------------------------------------------------------------------
    'about': {
        title: '<i class="fa-solid fa-building-shield mr-2"></i> About Lionsgate Network',
        body: `
            <div class="space-y-8 overflow-y-auto pr-2 max-h-[70vh]">
                <!-- Header Image Placeholder -->
                <div class="w-full h-48 bg-slate-800 rounded-lg flex items-center justify-center overflow-hidden relative">
                    <div class="absolute inset-0 bg-blue-900 opacity-50 mix-blend-multiply"></div>
                    <img src="/static/img/about_hero.jpg" alt="Lionsgate Network Operations" class="w-full h-full object-cover" onerror="this.style.display='none'">
                    <h2 class="relative text-3xl font-bold text-white z-10 tracking-widest uppercase">Securing The Chain</h2>
                </div>

                <div>
                    <p class="text-lg text-slate-700 leading-relaxed font-sans">Lionsgate Network is a premier blockchain intelligence and cybersecurity firm dedicated to illuminating the dark web. Our mission is to provide organizations, law enforcement, and enterprises with the operational clarity needed to navigate the complexities of Web3.</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="p-6 bg-slate-50 border border-slate-200 rounded-xl">
                        <h4 class="font-bold text-slate-800 mb-2"><i class="fa-solid fa-eye text-blue-600 mr-2"></i> Our Vision</h4>
                        <p class="text-sm text-slate-600">To create an internet where digital assets can be transacted safely, and malicious actors cannot hide behind cryptographic obfuscation.</p>
                    </div>
                    <div class="p-6 bg-slate-50 border border-slate-200 rounded-xl">
                        <h4 class="font-bold text-slate-800 mb-2"><i class="fa-solid fa-crosshairs text-blue-600 mr-2"></i> Our Mission</h4>
                        <p class="text-sm text-slate-600">Equipping global enforcement agencies with quantum-level tracing heuristics to recover stolen assets and dismantle cyber-syndicates.</p>
                    </div>
                </div>
            </div>
        `
    },
    'contact': {
        title: '<i class="fa-solid fa-envelope mr-2"></i> Contact Us',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <div class="text-center mb-8">
                    <h3 class="text-2xl font-bold text-slate-800">Secure Communications</h3>
                    <p class="text-sm text-slate-500 mt-2">Reach out to our intelligence analysts for platform support, partnership inquiries, or active investigation assistance.</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="border border-slate-200 p-6 rounded-lg text-center hover:border-blue-500 transition">
                        <i class="fa-solid fa-phone text-3xl text-blue-600 mb-4"></i>
                        <h4 class="font-bold text-slate-800">Direct Line</h4>
                        <p class="text-sm mt-2 text-slate-600">Available 24/7 for Enterprise Clients</p>
                    </div>
                    <div class="border border-slate-200 p-6 rounded-lg text-center hover:border-blue-500 transition">
                        <i class="fa-solid fa-envelope-open-text text-3xl text-blue-600 mb-4"></i>
                        <h4 class="font-bold text-slate-800">Email Support</h4>
                        <p class="text-sm mt-2 text-slate-600">support@lionsgate.network</p>
                    </div>
                </div>

                <div class="bg-slate-50 p-6 rounded-lg mt-6 text-center border border-slate-200">
                    <h4 class="font-bold text-slate-800 mb-2">Corporate Headquarters</h4>
                    <p class="text-sm text-slate-600">Tel Aviv, Israel</p>
                    <p class="text-xs text-slate-500 mt-2">Global operations coordinating with international law enforcement.</p>
                </div>
            </div>
        `
    },
    'project-nemesis': {
        title: '<i class="fa-solid fa-book-journal-whills mr-2"></i> Project NEMESIS: The Origin Story',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <div class="w-full h-40 bg-slate-900 rounded-lg flex items-center justify-center overflow-hidden relative mb-6">
                    <div class="absolute inset-0 bg-blue-900 opacity-30 mix-blend-multiply"></div>
                    <h2 class="relative text-4xl font-bold text-white z-10 tracking-[0.2em] uppercase" style="font-family: 'Chakra Petch', sans-serif;">PROJECT NEMESIS</h2>
                </div>

                <p class="text-sm">Born out of necessity, <strong>Project NEMESIS</strong> began when traditional blockchain explorers and tracing tools failed to keep pace with the hyper-velocity of modern cybercrime syndicates. As threat actors moved from simple Bitcoin transactions to complex, multi-chain smart contract exploits and zero-knowledge mixers, investigations that used to take days suddenly became impossible.</p>
                
                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mt-6">The Genesis</h4>
                <p class="text-sm">Lionsgate Intelligence Network recognized that tracing couldn't rely on human analysts clicking through block explorers. We needed a machine. A high-concurrency, multi-threaded engine capable of mapping thousands of asynchronous transactions across 12+ blockchains simultaneously. </p>
                <p class="text-sm">The result was the <strong>OmniChain Engine</strong>—the core of NEMESIS. Built on Python asynchronous I/O and backed by Scikit-Learn DBSCAN algorithms, NEMESIS doesn't just read the blockchain; it understands the <em>behavior</em> of the actors on it.</p>

                <h4 class="font-bold text-slate-800 text-lg border-b border-slate-200 pb-2 mt-6">From Shadows to Light</h4>
                <p class="text-sm">Today, NEMESIS stands as a premier enterprise intelligence platform. By integrating Darknet OSINT, deep-web scraping, and multi-chain heuristics into a single pane of glass, it transforms cryptographic noise into court-ready evidentiary dossiers. NEMESIS represents the absolute cutting-edge in the fight against decentralized financial crime.</p>
            </div>
        `
    },

    // ----------------------------------------------------------------------
    // 3. TECHNICAL & API DOCS
    // ----------------------------------------------------------------------
    'api-docs': {
        title: '<i class="fa-solid fa-code mr-2"></i> Developer API Reference',
        body: `
            <div class="space-y-6 font-mono text-sm overflow-y-auto max-h-[70vh] pr-2">
                <p class="text-slate-600 font-sans mb-4">NEMESIS provides a robust REST & WebSocket API for seamless integration with downstream platforms, SIEM pipelines, and enterprise automation.</p>
                
                <h4 class="font-bold text-slate-800 font-sans text-lg border-b border-slate-200 pb-2 mb-4">NEMESIS TRACER endpoints</h4>
                
                <div class="border border-slate-200 rounded-lg overflow-hidden mb-4">
                    <div class="bg-slate-100 px-4 py-2 border-b border-slate-200 font-bold text-slate-700 flex justify-between">
                        <span>POST /api/start_trace</span>
                        <span class="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200">ACTIVE</span>
                    </div>
                    <div class="p-4 bg-white space-y-2">
                        <p class="text-slate-600 text-xs font-sans">Initiates a new background OmniChain traversal execution.</p>
                        <div class="bg-slate-900 text-slate-300 p-3 rounded text-xs shadow-inner overflow-x-auto">
{
  "seeds": "0x123..., 0xabc...", 
  "target_amount": "5000", 
  "target_currency": "USD",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "chain_override": "AUTO",
  "max_depth": 12,
  "max_hops": 1000
}
                        </div>
                        <div class="text-xs mt-2"><span class="font-bold text-slate-700">Response:</span> <span class="text-blue-600">{"trace_id": "LGN-US-1718000000"}</span></div>
                    </div>
                </div>
                
                <div class="border border-slate-200 rounded-lg overflow-hidden mb-8">
                    <div class="bg-slate-100 px-4 py-2 border-b border-slate-200 font-bold text-slate-700 flex justify-between">
                        <span>WS /api/ws/{trace_id}</span>
                        <span class="text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded border border-purple-200">WEBSOCKET</span>
                    </div>
                    <div class="p-4 bg-white space-y-2">
                        <p class="text-slate-600 text-xs font-sans">Connect to the WebSocket stream to receive live graph physics events, database synchronizations, and terminal node resolution updates.</p>
                        <p class="text-xs text-slate-500 font-sans mt-2">Payload Events: <code>graph_update</code>, <code>log_update</code>, <code>trace_complete</code></p>
                    </div>
                </div>

                <h4 class="font-bold text-slate-800 font-sans text-lg border-b border-slate-200 pb-2 mb-4">NEMESIS ID endpoints</h4>

                <div class="border border-slate-200 rounded-lg overflow-hidden mb-4">
                    <div class="bg-slate-100 px-4 py-2 border-b border-slate-200 font-bold text-slate-700 flex justify-between">
                        <span>GET /api/nemesis_id/profile/{address}</span>
                        <span class="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded border border-blue-200">REST</span>
                    </div>
                    <div class="p-4 bg-white space-y-2">
                        <p class="text-slate-600 text-xs font-sans">Retrieves deep intelligence on a specific wallet using the Global Wallet Classification Taxonomy.</p>
                        <div class="bg-slate-900 text-slate-300 p-3 rounded text-xs shadow-inner overflow-x-auto">
// Output Schema
{
  "primary_classification": "Exchange Hot Wallet",
  "secondary_classifications": ["Custodian", "Liquidity Provider"],
  "risk_category": "High Risk",
  "risk_score": 92,
  "confidence": 0.97,
  "entity_type": "Organization",
  "operational_status": "Active",
  "tags": ["Binance", "Exchange", "Custodial", "High Velocity"]
}
                        </div>
                    </div>
                </div>
            </div>
        `
    },
    'knowledge-base': {
        title: '<i class="fa-solid fa-brain mr-2"></i> Knowledge Base & Scenarios',
        body: `
            <div class="space-y-6 text-slate-600 font-sans leading-relaxed">
                <p class="text-sm">Explore common investigation scenarios and how NEMESIS accelerates the resolution of complex blockchain crimes.</p>
                
                <div class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition">
                    <h4 class="font-bold text-slate-800 text-md mb-2"><i class="fa-solid fa-mask text-slate-500 mr-2"></i> Scenario 1: Deanonymizing Mixers</h4>
                    <p class="text-xs text-slate-600"><strong>The Problem:</strong> A threat actor routes stolen funds through Tornado Cash or a Bitcoin CoinJoin protocol to break the deterministic link.<br><br>
                    <strong>The NEMESIS Solution:</strong> Using heuristic clustering (DBSCAN) and timing analysis, NEMESIS analyzes deposits and withdrawals across the entire network timeline, identifying highly probable destination addresses based on gas fee patterns and withdrawal amounts.</p>
                </div>

                <div class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition mt-4">
                    <h4 class="font-bold text-slate-800 text-md mb-2"><i class="fa-solid fa-bridge text-blue-500 mr-2"></i> Scenario 2: Cross-Chain Bridge Hopping</h4>
                    <p class="text-xs text-slate-600"><strong>The Problem:</strong> Exploiters swap ETH for MATIC via a decentralized bridge, dropping the trail for standard single-chain explorers.<br><br>
                    <strong>The NEMESIS Solution:</strong> The OmniChain Engine detects the bridge contract interaction and automatically queries the destination chain (Polygon) via Enterprise RPCs, stitching the two disparate ledgers together seamlessly on the visual graph.</p>
                </div>

                <div class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition mt-4">
                    <h4 class="font-bold text-slate-800 text-md mb-2"><i class="fa-solid fa-file-pdf text-red-500 mr-2"></i> Scenario 3: Court-Ready Subpoenas</h4>
                    <p class="text-xs text-slate-600"><strong>The Problem:</strong> Law enforcement requires undeniable proof of fund movement to serve a freeze order on a Centralized Exchange.<br><br>
                    <strong>The NEMESIS Solution:</strong> The system automatically highlights the exact transaction hashes where funds hit known CEX deposit addresses and generates an immutable PDF Affidavit/Dossier containing the entire chain of custody.</p>
                </div>
            </div>
        `
    }
};

// Global function exposed to the window
window.openContentPage = function(pageName) {
    // If the data exists in our new global contentData
    let data = contentData[pageName];
    
    // Fallback logic for any objects defined strictly inside index.html's legacy contentData block
    if (!data && typeof window.legacyContentData !== 'undefined') {
        data = window.legacyContentData[pageName];
    }

    if(data) {
        document.getElementById('content-modal-title').innerHTML = data.title;
        document.getElementById('content-modal-body').innerHTML = data.body;
        document.getElementById('content-modal').classList.add('active');
    } else {
        console.error("Content page not found: " + pageName);
    }
};

window.closeContentPage = function() {
    document.getElementById('content-modal').classList.remove('active');
};
