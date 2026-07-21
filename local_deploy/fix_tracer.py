import os

TARGET = r"C:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis_tracer.html"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEMESIS TRACER</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://unpkg.com/layout-base/layout-base.js"></script>
    <script src="https://unpkg.com/cose-base/cose-base.js"></script>
    <script src="https://unpkg.com/cytoscape-fcose/cytoscape-fcose.js"></script>
    <script src="nemesis_graph_engine.js"></script>
    <script src="global_nav.js"></script>
    <link rel="stylesheet" href="nemesis-enterprise.css">

    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
                    colors: {
                        nemblue: '#4f46e5',
                        nempurple: '#7c3aed',
                        nemcyan: '#06b6d4',
                    },
                    backgroundImage: {
                        'holo-gradient': 'radial-gradient(circle at 50% 50%, rgba(243, 244, 246, 1) 0%, rgba(224, 231, 255, 0.4) 50%, rgba(245, 243, 255, 0.8) 100%)',
                    }
                }
            }
        }
    </script>
    <style>
        body { 
            margin: 0; padding: 0; overflow: hidden; height: 100vh; display: flex; flex-direction: column; 
            background: #f8f9fa;
        }
        
        /* Global Ambient Glow */
        .ambient-bg {
            position: fixed; inset: 0; z-index: -1;
            background: 
                radial-gradient(circle at 15% 50%, rgba(124, 58, 237, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 85% 30%, rgba(59, 130, 246, 0.08) 0%, transparent 50%);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        
        .glass-panel { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); }
        .solid-card { background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03); border: 1px solid rgba(226, 232, 240, 0.8); }
        
        #network-graph { width: 100%; height: 100%; outline: none; }
        
        /* Sidebar active link */
        .nav-link { color: #64748b; font-weight: 600; padding: 0.75rem 1rem; border-radius: 12px; transition: all 0.3s; display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem; font-size: 0.85rem; }
        .nav-link:hover { background: rgba(241, 245, 249, 0.8); color: #0f172a; }
        .nav-link.active { background: linear-gradient(90deg, rgba(238,242,255,1) 0%, rgba(255,255,255,1) 100%); color: #4f46e5; border-left: 4px solid #4f46e5; box-shadow: 0 2px 10px rgba(79, 70, 229, 0.1); }
        
        /* Metric Cards */
        .metric-title { font-size: 0.65rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
        .metric-value { font-size: 1.5rem; font-weight: 900; color: #0f172a; letter-spacing: -0.02em; }
        .metric-icon-wrapper { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }

        /* Flow Timeline */
        .timeline-item { position: relative; padding-left: 1.5rem; padding-bottom: 1rem; }
        .timeline-item::before { content: ''; position: absolute; left: 0; top: 0.25rem; width: 0.75rem; height: 0.75rem; border-radius: 50%; border: 2px solid; background: white; z-index: 2; }
        .timeline-item::after { content: ''; position: absolute; left: 0.375rem; top: 1rem; bottom: 0; width: 2px; background: #e2e8f0; z-index: 1; }
        .timeline-item:last-child::after { display: none; }
        .tl-blue::before { border-color: #3b82f6; }
        .tl-orange::before { border-color: #f59e0b; }
        .tl-purple::before { border-color: #8b5cf6; }
    </style>
</head>
<body class="text-slate-800 font-sans">
    
    <div class="ambient-bg"></div>

    <!-- Main Flex Container -->
    <div class="flex h-screen w-full overflow-hidden">

        <!-- Left Sidebar -->
        <aside class="w-[260px] glass-panel flex flex-col flex-shrink-0 z-20 m-3 mr-0 rounded-2xl overflow-hidden">
            <!-- Logo -->
            <div class="p-5 flex items-center gap-3 cursor-pointer border-b border-slate-100/50" onclick="window.location.href='index.html'">
                <div class="w-10 h-10 flex items-center justify-center text-2xl drop-shadow-[0_0_8px_rgba(124,58,237,0.4)]">
                    🦋
                </div>
                <div>
                    <h1 class="text-lg font-black tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-nemblue to-nempurple leading-none">NEMESIS</h1>
                    <p class="text-[8px] text-slate-500 font-bold tracking-widest mt-0.5 uppercase">Intelligence Network</p>
                </div>
            </div>

            <!-- Navigation -->
            <div class="p-3 flex-1 overflow-y-auto">
                <a href="dashboard.html" class="nav-link"><i class="fa-solid fa-house w-5"></i> Dashboard</a>
                <a href="#" class="nav-link"><i class="fa-solid fa-magnifying-glass w-5"></i> Investigations</a>
                <a href="nemesis_tracer.html" class="nav-link active"><i class="fa-solid fa-network-wired w-5"></i> Tracer</a>
                <a href="nemesis_id.html" class="nav-link"><i class="fa-solid fa-fingerprint w-5"></i> Entities</a>
                <a href="#" class="nav-link"><i class="fa-solid fa-bell w-5"></i> Alerts <span class="ml-auto bg-nempurple text-white text-[10px] px-2 py-0.5 rounded-full">24</span></a>
                <a href="nemesis_threat_hunter.html" class="nav-link"><i class="fa-solid fa-satellite-dish w-5"></i> Intel Feeds</a>
                
                <div class="mt-6 mb-2 px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tools</div>
                <a href="#" class="nav-link"><i class="fa-solid fa-file-contract w-5"></i> Reports</a>
                <a href="#" class="nav-link"><i class="fa-solid fa-star w-5"></i> Watchlists</a>
                <a href="#" class="nav-link"><i class="fa-solid fa-gavel w-5"></i> Sanctions</a>
                <a href="#" class="nav-link"><i class="fa-solid fa-brain w-5"></i> AI Intelligence</a>
            </div>

            <!-- AI Assistant Orb Widget -->
            <div class="m-3 p-4 rounded-xl bg-gradient-to-br from-[#0f172a] to-[#1e1b4b] text-white relative overflow-hidden shadow-[0_10px_20px_rgba(30,27,75,0.4)] border border-slate-700">
                <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                <div class="relative z-10 flex flex-col items-center text-center">
                    <div class="w-16 h-16 rounded-full border-4 border-indigo-500/30 flex items-center justify-center mb-2 shadow-[0_0_15px_rgba(99,102,241,0.6)] bg-black/50">
                        <span class="text-2xl drop-shadow-[0_0_8px_rgba(167,139,250,1)]">🦋</span>
                    </div>
                    <div class="text-[10px] font-bold text-indigo-300 flex items-center gap-1 mb-1">
                        <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> AI Assistant Online
                    </div>
                    <div class="text-xs text-slate-300">Analyzing blockchain...</div>
                </div>
            </div>
        </aside>

        <!-- Center Content -->
        <main class="flex-1 flex flex-col relative z-10 p-3 pt-4 gap-3 h-screen overflow-hidden">
            
            <!-- Top Header & Search -->
            <header class="flex items-center justify-between px-2 flex-shrink-0">
                <!-- Search Bar -->
                <div class="relative w-full max-w-2xl">
                    <i class="fa-solid fa-search absolute left-4 top-1/2 transform -translate-y-1/2 text-nempurple"></i>
                    <input type="text" placeholder="Search by address, tx hash, token, domain, entity..." class="w-full pl-10 pr-4 py-2.5 rounded-full border border-slate-200 bg-white/80 backdrop-blur-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-nempurple/50 focus:bg-white transition-all">
                    <span class="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-400 text-xs font-bold bg-slate-100 px-1.5 rounded">/</span>
                </div>

                <!-- Right Actions -->
                <div class="flex items-center gap-4">
                    <button class="relative w-10 h-10 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-nempurple shadow-sm flex items-center justify-center transition">
                        <i class="fa-solid fa-bell"></i>
                        <span class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] rounded-full flex items-center justify-center font-bold">12</span>
                    </button>
                    <button class="w-10 h-10 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-nempurple shadow-sm flex items-center justify-center transition"><i class="fa-solid fa-moon"></i></button>
                    <button class="w-10 h-10 rounded-full bg-white border border-slate-200 text-slate-600 hover:text-nempurple shadow-sm flex items-center justify-center transition"><i class="fa-solid fa-globe"></i></button>
                    
                    <div class="flex items-center gap-3 bg-white border border-slate-200 pl-2 pr-4 py-1.5 rounded-full shadow-sm cursor-pointer hover:border-nempurple transition">
                        <div class="w-8 h-8 rounded-full bg-slate-200 overflow-hidden">
                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Alex" alt="Avatar">
                        </div>
                        <div class="text-right">
                            <div class="text-xs font-bold text-slate-800 leading-tight">Alex Chen</div>
                            <div class="text-[9px] text-slate-500 font-semibold">Administrator</div>
                        </div>
                        <i class="fa-solid fa-chevron-down text-slate-400 text-[10px] ml-2"></i>
                    </div>
                </div>
            </header>

            <!-- Top Metric Cards Row -->
            <div class="grid grid-cols-4 gap-3 flex-shrink-0">
                <!-- Card 1 -->
                <div class="solid-card p-4 flex flex-col justify-between relative overflow-hidden">
                    <div class="flex justify-between items-start mb-2">
                        <div class="metric-title">Total Value Tracked</div>
                        <div class="metric-icon-wrapper bg-purple-50 text-purple-500"><i class="fa-regular fa-user"></i></div>
                    </div>
                    <div class="metric-value">$865,737.47</div>
                    <div class="flex justify-between items-end mt-1">
                        <div class="text-[10px] text-slate-400 font-bold">USD</div>
                        <div class="text-xs text-green-600 font-bold"><i class="fa-solid fa-caret-up"></i> 12.45%</div>
                    </div>
                </div>

                <!-- Card 2 -->
                <div class="solid-card p-4 flex flex-col justify-between relative overflow-hidden">
                    <div class="flex justify-between items-start mb-2">
                        <div class="metric-title">Known Entities</div>
                        <div class="metric-icon-wrapper bg-blue-50 text-blue-500"><i class="fa-solid fa-users"></i></div>
                    </div>
                    <div class="metric-value">18</div>
                    <div class="flex justify-between items-end mt-1">
                        <div class="text-[10px] text-slate-400 font-bold">Identified</div>
                        <div class="text-xs text-green-600 font-bold"><i class="fa-solid fa-caret-up"></i> 8.31%</div>
                    </div>
                </div>

                <!-- Card 3 -->
                <div class="solid-card p-4 flex flex-col justify-between relative overflow-hidden">
                    <div class="flex justify-between items-start mb-2">
                        <div class="metric-title">Unknown Wallets</div>
                        <div class="metric-icon-wrapper bg-pink-50 text-pink-500"><i class="fa-solid fa-question"></i></div>
                    </div>
                    <div class="metric-value">42</div>
                    <div class="flex justify-between items-end mt-1">
                        <div class="text-[10px] text-slate-400 font-bold">Unidentified</div>
                        <div class="text-xs text-red-500 font-bold"><i class="fa-solid fa-caret-down"></i> 5.27%</div>
                    </div>
                </div>

                <!-- Card 4 -->
                <div class="solid-card p-4 flex flex-col justify-between relative overflow-hidden">
                    <div class="flex justify-between items-start mb-2">
                        <div class="metric-title">Exchanges / Mixers</div>
                        <div class="flex gap-1">
                            <div class="metric-icon-wrapper bg-orange-50 text-orange-500"><i class="fa-solid fa-building-columns"></i></div>
                            <div class="metric-icon-wrapper bg-red-50 text-red-500"><i class="fa-solid fa-shield-halved"></i></div>
                        </div>
                    </div>
                    <div class="flex gap-6 mt-1">
                        <div>
                            <div class="metric-value">6</div>
                            <div class="text-[10px] text-slate-400 font-bold">CEX</div>
                        </div>
                        <div>
                            <div class="metric-value">2</div>
                            <div class="text-[10px] text-slate-400 font-bold">Mixers</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Graph Area -->
            <div class="flex-1 solid-card relative overflow-hidden flex flex-col bg-gradient-to-br from-[#fafafa] to-[#f3f4f6]">
                <!-- Graph Header Options -->
                <div class="absolute top-4 left-4 right-4 z-10 flex justify-between pointer-events-none">
                    <div class="bg-white/80 backdrop-blur pointer-events-auto px-3 py-1.5 rounded-lg shadow-sm border border-slate-200 text-xs font-bold text-slate-600 flex items-center gap-2">
                        <i class="fa-solid fa-circle-nodes text-nemblue"></i> NETWORK GRAPH
                    </div>
                    <div class="flex gap-2 pointer-events-auto">
                        <button class="bg-white px-3 py-1.5 rounded-lg shadow-sm border border-slate-200 text-xs font-bold text-slate-600 hover:text-nemblue transition">All Chains <i class="fa-solid fa-chevron-down ml-1"></i></button>
                        <button class="w-8 h-8 rounded-lg bg-white shadow-sm border border-slate-200 text-slate-600 hover:text-nemblue flex items-center justify-center"><i class="fa-solid fa-filter"></i></button>
                        <button class="w-8 h-8 rounded-lg bg-white shadow-sm border border-slate-200 text-slate-600 hover:text-nemblue flex items-center justify-center"><i class="fa-solid fa-expand"></i></button>
                    </div>
                </div>

                <div class="flex-1 w-full h-full relative" id="network-container">
                    <div id="network-graph"></div>
                </div>

                <!-- Legend bottom -->
                <div class="absolute bottom-4 left-4 bg-white/90 backdrop-blur px-4 py-2 rounded-xl shadow-sm border border-slate-200 flex gap-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider z-10">
                    <div class="flex items-center gap-1"><span class="w-4 h-4 rounded-full bg-orange-100 flex items-center justify-center"><i class="fa-solid fa-building-columns text-[8px] text-orange-500"></i></span> Exchange</div>
                    <div class="flex items-center gap-1"><span class="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center"><i class="fa-solid fa-wallet text-[8px] text-blue-500"></i></span> Wallet</div>
                    <div class="flex items-center gap-1"><span class="w-4 h-4 rounded-full bg-indigo-100 flex items-center justify-center"><i class="fa-solid fa-file-contract text-[8px] text-indigo-500"></i></span> Contract</div>
                    <div class="flex items-center gap-1"><span class="w-4 h-4 rounded-full bg-red-100 flex items-center justify-center"><i class="fa-solid fa-shield-virus text-[8px] text-red-500"></i></span> High Risk</div>
                    <div class="w-px h-4 bg-slate-200 mx-1"></div>
                    <div class="flex items-center gap-1 text-nemblue"><i class="fa-solid fa-arrow-right"></i> Inflow</div>
                    <div class="flex items-center gap-1 text-pink-500"><i class="fa-solid fa-arrow-right"></i> Outflow</div>
                </div>
            </div>

            <!-- Bottom Table -->
            <div class="h-56 solid-card flex flex-col flex-shrink-0 overflow-hidden">
                <div class="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                    <h3 class="font-bold text-xs text-slate-700 tracking-wider uppercase">Transaction Intelligence</h3>
                </div>
                <div class="flex-1 overflow-auto">
                    <table class="w-full text-left border-collapse text-[11px]">
                        <thead class="sticky top-0 bg-slate-50 border-b border-slate-200 shadow-sm z-10">
                            <tr class="font-bold text-slate-500 uppercase tracking-wider">
                                <th class="py-2 px-4">Date / Time (UTC)</th>
                                <th class="py-2 px-4">Tx Hash</th>
                                <th class="py-2 px-4">From</th>
                                <th class="py-2 px-4 text-center"></th>
                                <th class="py-2 px-4">To</th>
                                <th class="py-2 px-4">Asset</th>
                                <th class="py-2 px-4 text-right">Amount (USD)</th>
                                <th class="py-2 px-4">Risk</th>
                                <th class="py-2 px-4">Confidence</th>
                                <th class="py-2 px-4">AI Insight</th>
                            </tr>
                        </thead>
                        <tbody class="font-medium text-slate-600 bg-white">
                            <tr class="border-b border-slate-50 hover:bg-slate-50 transition cursor-pointer">
                                <td class="py-2.5 px-4 text-slate-500">May 18, 2024 10:25:33</td>
                                <td class="py-2.5 px-4 text-nemblue font-mono">0xa212...7ccd9</td>
                                <td class="py-2.5 px-4 font-bold text-slate-800">Seed Wallet <span class="block text-[9px] text-slate-400 font-normal">[External]</span></td>
                                <td class="py-2.5 px-2 text-center text-slate-300"><i class="fa-solid fa-arrow-right"></i></td>
                                <td class="py-2.5 px-4 font-bold text-slate-800">0x8f3a...7c2e4b <span class="block text-[9px] text-blue-400 font-normal bg-blue-50 px-1 inline-block rounded border border-blue-100 mt-0.5">[Internal]</span></td>
                                <td class="py-2.5 px-4"><div class="flex items-center gap-1.5"><span class="w-5 h-5 rounded-full bg-orange-100 text-orange-500 flex items-center justify-center text-[10px]"><i class="fa-brands fa-bitcoin"></i></span> BTC</div></td>
                                <td class="py-2.5 px-4 text-right font-bold text-slate-800">$865,737.47 <span class="block text-[9px] text-slate-400 font-normal">(12.5376 BTC)</span></td>
                                <td class="py-2.5 px-4"><span class="bg-red-50 text-red-600 border border-red-100 font-bold px-1.5 py-0.5 rounded text-[10px]">85</span></td>
                                <td class="py-2.5 px-4 font-bold text-green-500">97%</td>
                                <td class="py-2.5 px-4 text-slate-500 max-w-[150px] truncate">High value inflow from external wallet</td>
                            </tr>
                            <tr class="border-b border-slate-50 hover:bg-slate-50 transition cursor-pointer">
                                <td class="py-2.5 px-4 text-slate-500">May 18, 2024 10:25:43</td>
                                <td class="py-2.5 px-4 text-nemblue font-mono">0x4f18...1a0s3</td>
                                <td class="py-2.5 px-4 font-bold text-slate-800">0x8f3a...7c2e4b <span class="block text-[9px] text-blue-400 font-normal bg-blue-50 px-1 inline-block rounded border border-blue-100 mt-0.5">[Internal]</span></td>
                                <td class="py-2.5 px-2 text-center text-slate-300"><i class="fa-solid fa-arrow-right"></i></td>
                                <td class="py-2.5 px-4 font-bold text-slate-800">WBTC (ERC20) <span class="block text-[9px] text-indigo-400 font-normal bg-indigo-50 px-1 inline-block rounded border border-indigo-100 mt-0.5">[Smart Contract]</span></td>
                                <td class="py-2.5 px-4"><div class="flex items-center gap-1.5"><span class="w-5 h-5 rounded-full bg-slate-800 text-slate-200 flex items-center justify-center text-[10px]"><i class="fa-brands fa-bitcoin"></i></span> WBTC</div></td>
                                <td class="py-2.5 px-4 text-right font-bold text-slate-800">$865,729.19 <span class="block text-[9px] text-slate-400 font-normal">(12.5376 WBTC)</span></td>
                                <td class="py-2.5 px-4"><span class="bg-orange-50 text-orange-600 border border-orange-100 font-bold px-1.5 py-0.5 rounded text-[10px]">78</span></td>
                                <td class="py-2.5 px-4 font-bold text-green-500">96%</td>
                                <td class="py-2.5 px-4 text-slate-500 max-w-[150px] truncate">Wrapped BTC on Ethereum network</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </main>

        <!-- Right Sidebar (Entity & Timeline) -->
        <aside class="w-[300px] flex flex-col flex-shrink-0 z-20 m-3 ml-0 gap-3">
            
            <!-- Confidence / Entity Details -->
            <div class="solid-card p-4 flex-1 flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-[10px] text-slate-500 tracking-widest uppercase">Confidence Score</h3>
                    <div class="flex gap-1 text-slate-400">
                        <i class="fa-solid fa-chart-line cursor-pointer hover:text-nemblue text-xs"></i>
                        <i class="fa-solid fa-gear cursor-pointer hover:text-nemblue text-xs"></i>
                    </div>
                </div>

                <div class="flex items-center gap-3 mb-4">
                    <div class="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-500 to-nempurple flex items-center justify-center text-white shadow-lg">
                        <i class="fa-solid fa-wallet"></i>
                    </div>
                    <div>
                        <div class="font-black text-lg text-slate-800 font-mono tracking-tight flex items-center gap-2">
                            0x8f3a...7c2e4b <i class="fa-regular fa-copy text-[10px] text-slate-400 cursor-pointer hover:text-nemblue"></i>
                        </div>
                        <div class="bg-indigo-50 text-nemblue text-[10px] font-bold px-2 py-0.5 rounded border border-indigo-100 inline-block mt-0.5">EOA Wallet</div>
                        <div class="bg-green-50 text-green-600 text-[10px] font-bold px-2 py-0.5 rounded border border-green-100 inline-block mt-0.5 ml-1"><i class="fa-solid fa-check mr-1"></i>Verified</div>
                    </div>
                </div>

                <div class="space-y-3 text-xs flex-1">
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Entity Type</span> <span class="font-bold text-slate-800">Wallet</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Label</span> <span class="font-bold text-slate-800">Binance Deposit</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Cluster</span> <span class="font-bold text-slate-800">C-12345</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Risk Score</span> <span class="font-bold text-red-500 bg-red-50 px-1.5 py-0.5 rounded">85 - High Risk</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">First Seen</span> <span class="font-mono text-slate-700">2021-03-12 08:21:45</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Last Seen</span> <span class="font-mono text-slate-700">2024-05-20 14:32:11</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Total Received</span> <span class="font-mono font-bold text-slate-800">12,432.88 ETH</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Total Sent</span> <span class="font-mono font-bold text-slate-800">12,338.88 ETH</span></div>
                    <div class="flex justify-between border-b border-slate-50 pb-2"><span class="text-slate-500">Transactions</span> <span class="font-mono font-bold text-slate-800">3,721</span></div>
                    <div class="flex justify-between items-center"><span class="text-slate-500">Chains</span> 
                        <div class="flex gap-1 text-[10px]">
                            <span class="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center text-blue-500"><i class="fa-brands fa-ethereum"></i></span>
                            <span class="w-4 h-4 rounded-full bg-orange-100 flex items-center justify-center text-orange-500">B</span>
                            <span class="w-4 h-4 rounded-full bg-purple-100 flex items-center justify-center text-purple-500">P</span>
                        </div>
                    </div>
                </div>

                <button class="w-full mt-3 text-nemblue font-bold text-xs uppercase tracking-widest py-2 hover:bg-slate-50 rounded transition flex items-center justify-center gap-2">
                    View Full Profile <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>

            <!-- Flow Timeline -->
            <div class="solid-card p-4 flex-1 flex flex-col">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-[10px] text-slate-500 tracking-widest uppercase">Flow Timeline</h3>
                    <div class="flex gap-2 text-slate-400">
                        <i class="fa-solid fa-expand cursor-pointer hover:text-nemblue text-xs"></i>
                        <i class="fa-solid fa-gear cursor-pointer hover:text-nemblue text-xs"></i>
                    </div>
                </div>

                <div class="flex-1 overflow-y-auto pr-2">
                    <div class="timeline-item tl-orange">
                        <div class="text-[9px] text-slate-400 font-mono mb-0.5">May 18, 2024 10:25:33</div>
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="text-xs font-bold text-slate-800">BTC sent from Seed Wallet</div>
                                <div class="text-xs font-bold text-green-600">$865,737.47</div>
                            </div>
                            <div class="w-5 h-5 rounded-full bg-orange-100 text-orange-500 flex items-center justify-center text-[8px]"><i class="fa-brands fa-bitcoin"></i></div>
                        </div>
                    </div>
                    
                    <div class="timeline-item tl-blue">
                        <div class="text-[9px] text-slate-400 font-mono mb-0.5">May 18, 2024 10:25:43</div>
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="text-xs font-bold text-slate-800">Converted to WBTC</div>
                                <div class="text-xs font-bold text-green-600">$865,737.18</div>
                            </div>
                            <div class="w-5 h-5 rounded-full bg-slate-800 text-white flex items-center justify-center text-[8px]"><i class="fa-brands fa-bitcoin"></i></div>
                        </div>
                    </div>
                    
                    <div class="timeline-item tl-purple">
                        <div class="text-[9px] text-slate-400 font-mono mb-0.5">May 18, 2024 10:29:22</div>
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="text-xs font-bold text-slate-800">WBTC swapped to ETH</div>
                                <div class="text-xs font-bold text-green-600">$865,721.24</div>
                            </div>
                            <div class="w-5 h-5 rounded-full bg-indigo-100 text-indigo-500 flex items-center justify-center text-[8px]"><i class="fa-brands fa-ethereum"></i></div>
                        </div>
                    </div>
                    
                    <div class="timeline-item tl-blue">
                        <div class="text-[9px] text-slate-400 font-mono mb-0.5">May 18, 2024 10:31:18</div>
                        <div class="flex items-start justify-between">
                            <div>
                                <div class="text-xs font-bold text-slate-800">ETH bridged to Base</div>
                                <div class="text-xs font-bold text-green-600">$865,700.12</div>
                            </div>
                            <div class="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-[8px]"><i class="fa-solid fa-bridge-water"></i></div>
                        </div>
                    </div>
                </div>

                <button class="w-full mt-2 text-nemblue font-bold text-xs uppercase tracking-widest py-2 hover:bg-slate-50 rounded transition flex items-center justify-center gap-2 border-t border-slate-100">
                    View Full Timeline <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>

        </aside>

    </div>

    <!-- NEMESIS ID SLIDING PANEL INTEGRATION -->
    <div id="nemesis-id-panel" class="fixed top-0 right-0 h-screen w-[60vw] max-w-[1200px] bg-white/95 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.2)] translate-x-full transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] z-[9999] border-l border-slate-200/50 flex flex-col">
        <div class="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-white">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-fingerprint text-nempurple text-xl"></i>
                <h2 class="font-black text-lg text-slate-800 tracking-widest">NEMESIS ID <span class="font-normal text-slate-400">| KERNEL</span></h2>
            </div>
            <button id="close-panel-btn" class="w-10 h-10 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-red-500 transition shadow-sm border border-slate-200"><i class="fa-solid fa-xmark text-lg"></i></button>
        </div>
        <div class="flex-1 w-full relative bg-slate-50">
            <!-- Iframe embed to guarantee 100% stylistic and functional fidelity of the ID Dashboard without JS collisions -->
            <iframe id="nemesis-id-frame" src="" class="absolute inset-0 w-full h-full border-0"></iframe>
        </div>
    </div>

    <!-- Cytoscape Graph Implementation -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            
            // Reconstruct the exact nodes shown in the beautiful graph
            const elements = [
                // Center Node
                { data: { id: 'center', label: '0x8f3a...7c2e4b\\nEOA Wallet' } },
                
                // Top Node (High Risk)
                { data: { id: 'hr1', label: 'High Risk Entity\\n0x7bfe...a9d21f' } },
                { data: { source: 'hr1', target: 'center', label: '' }, classes: 'edge-red' },

                // Top Left (Binance)
                { data: { id: 'binance', label: 'Binance\\n0x28c6...c68d76' } },
                { data: { source: 'binance', target: 'center', label: '37 txs\\n$865,731.47' }, classes: 'edge-blue' },

                // Top Right (Coinbase)
                { data: { id: 'coinbase', label: 'Coinbase\\n0x9996...7d7a50' } },
                { data: { source: 'center', target: 'coinbase', label: '12 txs\\n$66,721.94' }, classes: 'edge-purple' },

                // Left (Uniswap)
                { data: { id: 'uniswap', label: 'Uniswap V3\\n0xe592...1564' } },
                { data: { source: 'center', target: 'uniswap', label: '5 txs\\n$56,492.01' }, classes: 'edge-green' },

                // Right (Base Bridge)
                { data: { id: 'bridge', label: 'Base Bridge\\n0x4200...0006' } },
                { data: { source: 'center', target: 'bridge', label: '8 txs\\n$65,700.12' }, classes: 'edge-blue' },

                // Bottom Left (USDT)
                { data: { id: 'usdt', label: 'USDT (TRC20)\\nTAh8xH...7uZt' } },
                { data: { source: 'usdt', target: 'center', label: '26 txs\\n$256,492.01' }, classes: 'edge-green' },

                // Bottom (Smart Contract)
                { data: { id: 'contract', label: 'Smart Contract\\n0x4a2b...9f8e7d' } },
                { data: { source: 'contract', target: 'center', label: '9 txs\\n$13,221.44' }, classes: 'edge-purple' },

                // Bottom Right (ETH)
                { data: { id: 'eth', label: 'ETH (ERC20)\\n0xC02a...6Cc2' } },
                { data: { source: 'center', target: 'eth', label: '15 txs\\n$865,700.12' }, classes: 'edge-blue' }
            ];

            const cy = cytoscape({
                container: document.getElementById('network-graph'),
                elements: elements,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'width': 60,
                            'height': 60,
                            'background-color': '#fff',
                            'border-width': 4,
                            'border-color': '#3b82f6',
                            'label': 'data(label)',
                            'text-wrap': 'wrap',
                            'text-valign': 'bottom',
                            'text-halign': 'center',
                            'text-margin-y': 8,
                            'font-size': '10px',
                            'font-weight': 'bold',
                            'font-family': 'Inter',
                            'color': '#1e293b',
                            'text-background-opacity': 1,
                            'text-background-color': 'rgba(255,255,255,0.8)',
                            'text-background-padding': 4,
                            'text-background-shape': 'roundrectangle'
                        }
                    },
                    {
                        selector: 'node[id="center"]',
                        style: {
                            'width': 80,
                            'height': 80,
                            'border-width': 0,
                            'background-image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Ethereum_logo_2014.svg/1257px-Ethereum_logo_2014.svg.png',
                            'background-fit': 'cover',
                            'background-color': '#4f46e5',
                            'underlay-color': '#4f46e5',
                            'underlay-padding': 15,
                            'underlay-opacity': 0.3,
                            'underlay-shape': 'ellipse'
                        }
                    },
                    {
                        selector: 'node[id="hr1"]',
                        style: { 'border-color': '#ef4444' }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#94a3b8',
                            'target-arrow-color': '#94a3b8',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '8px',
                            'font-weight': 'bold',
                            'color': '#475569',
                            'text-background-opacity': 1,
                            'text-background-color': 'rgba(255,255,255,0.9)',
                            'text-background-padding': 2
                        }
                    },
                    {
                        selector: 'edge.edge-blue',
                        style: { 'line-color': '#3b82f6', 'target-arrow-color': '#3b82f6' }
                    },
                    {
                        selector: 'edge.edge-red',
                        style: { 'line-color': '#ef4444', 'target-arrow-color': '#ef4444' }
                    },
                    {
                        selector: 'edge.edge-purple',
                        style: { 'line-color': '#8b5cf6', 'target-arrow-color': '#8b5cf6' }
                    },
                    {
                        selector: 'edge.edge-green',
                        style: { 'line-color': '#10b981', 'target-arrow-color': '#10b981' }
                    }
                ],
                layout: {
                    name: 'circle',
                    padding: 50
                }
            });

            // Re-center Center Node
            cy.nodes('#center').position({ x: cy.width() / 2, y: cy.height() / 2 });
            cy.layout({ name: 'preset' }).run();

            // Sliding Panel Logic for NEMESIS ID integration
            const panel = document.getElementById('nemesis-id-panel');
            const iframe = document.getElementById('nemesis-id-frame');
            const closeBtn = document.getElementById('close-panel-btn');

            cy.on('tap', 'node', function(evt){
                const node = evt.target;
                const labelLines = node.data('label').split('\\n');
                let addr = labelLines[labelLines.length - 1]; // Use the bottom line as the address
                if(addr.includes('Wallet') || addr.includes('Contract') || addr.includes('Exchange')) {
                    addr = labelLines[0]; // fallback
                }
                
                // Embed the NEMESIS ID dashboard into the iframe!
                // Assuming nemesis_id_new.html handles URL params gracefully:
                iframe.src = `nemesis_id_new.html?address=${encodeURIComponent(addr)}`;
                
                // Slide in
                panel.classList.remove('translate-x-full');
            });

            closeBtn.addEventListener('click', () => {
                panel.classList.add('translate-x-full');
                setTimeout(() => { iframe.src = ''; }, 500); // Clear iframe memory after animation
            });
        });
    </script>
</body>
</html>
"""

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)
    
print("Successfully generated and replaced nemesis_tracer.html with Holographic UI and Sliding Panel Integration!")
