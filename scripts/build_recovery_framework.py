import os

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cryptocurrency Asset Recovery Framework | Lionsgate Network</title>
    
    <!-- Dependencies -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/output.css" rel="stylesheet">

    <style>
        /* Base Variables & Theming */
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --surface: #ffffff;
            --background: #0f172a; /* Dark background to match NEMESIS */
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }

        body { 
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            background-color: var(--background); 
            color: var(--text-main); 
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        /* Custom Scrollbar */
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #64748b; }

        /* WebGL Background */
        #webgl-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            opacity: 0.3;
            pointer-events: none;
        }

        /* Top Header (NEMESIS Style) */
        header {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .nav-link {
            color: #94a3b8;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.1em;
            transition: all 0.3s ease;
        }
        .nav-link:hover { color: #38bdf8; text-shadow: 0 0 10px rgba(56,189,248,0.5); }

        /* Main Container */
        .app-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        /* Sidebar Navigation */
        #sidebar {
            width: 320px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        .sidebar-header {
            padding: 24px;
            border-bottom: 1px solid var(--border);
        }

        .nav-menu {
            flex: 1;
            padding: 16px 0;
        }

        .nav-item {
            padding: 10px 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-muted);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
            cursor: pointer;
        }

        .nav-item:hover { background: rgba(255,255,255,0.05); color: #e2e8f0; }
        .nav-item.active { color: #38bdf8; background: rgba(56,189,248,0.1); border-left-color: #38bdf8; font-weight: 600; }
        .nav-group-title { padding: 20px 24px 8px; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; font-weight: 800; }

        /* Main Content Area */
        #main-content {
            flex: 1;
            overflow-y: auto;
            padding: 40px;
            scroll-behavior: smooth;
        }

        .content-section { display: none; animation: fadeIn 0.4s ease-out; max-width: 1000px; margin: 0 auto; }
        .content-section.active { display: block; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

        /* Legal Document Style (White Paper Look) */
        .legal-document {
            background: white;
            padding: 80px;
            border-radius: 4px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            font-family: 'Merriweather', serif;
            color: #1e293b;
            line-height: 1.7;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }

        .legal-document::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 12px;
            background: linear-gradient(90deg, #1e293b, #3b82f6, #1e293b);
        }

        /* LIONSGATE WATERMARK */
        .watermark {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-family: 'Inter', sans-serif;
            font-size: 8rem;
            font-weight: 900;
            color: rgba(0, 0, 0, 0.03);
            white-space: nowrap;
            pointer-events: none;
            z-index: 0;
            user-select: none;
        }

        /* Typography within Docs */
        .legal-document h1, .legal-document h2, .legal-document h3, .legal-document h4 { font-family: 'Inter', sans-serif; color: #0f172a; position: relative; z-index: 1; }
        .legal-document h1 { font-size: 2.2rem; font-weight: 900; border-bottom: 3px solid #0f172a; padding-bottom: 16px; margin-bottom: 40px; text-transform: uppercase; letter-spacing: -0.02em; text-align: center;}
        .legal-document h2 { font-size: 1.4rem; font-weight: 800; margin-top: 40px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; color: #1e293b;}
        .legal-document h3 { font-size: 1.1rem; font-weight: 700; margin-top: 24px; margin-bottom: 12px; color: #334155; }
        .legal-document p { margin-bottom: 16px; position: relative; z-index: 1; text-align: justify; }
        .legal-document ul { margin-bottom: 20px; padding-left: 24px; list-style-type: disc; position: relative; z-index: 1; }
        .legal-document li { margin-bottom: 8px; }
        .legal-document strong { color: #0f172a; font-weight: 700; }

        /* Print Button Floating */
        .print-actions { position: sticky; top: 20px; display: flex; justify-content: flex-end; margin-bottom: 20px; z-index: 100; }
        .btn-print { background: #0f172a; color: white; padding: 10px 24px; border-radius: 6px; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); transition: all 0.2s; cursor: pointer; border: none; }
        .btn-print:hover { background: #2563eb; transform: translateY(-2px); box-shadow: 0 6px 15px -2px rgba(37, 99, 235, 0.3); }

        /* SVG Flowchart Animations */
        .flow-path { stroke-dasharray: 10; animation: dash 20s linear infinite; }
        @keyframes dash { to { stroke-dashoffset: -1000; } }
        .flow-node { transition: all 0.3s; cursor: default; }
        .flow-node:hover { filter: drop-shadow(0px 10px 15px rgba(37,99,235,0.3)); transform: scale(1.02); }

        /* Print Styles */
        @media print {
            body { background: white; height: auto; display: block; overflow: visible;}
            header, #sidebar, #webgl-canvas, .print-actions { display: none !important; }
            .app-container { display: block; }
            #main-content { padding: 0; overflow: visible; }
            .content-section { display: none; max-width: 100%; margin: 0; }
            .content-section.active { display: block; }
            .legal-document { box-shadow: none; border: none; padding: 0; margin: 0; }
            .legal-document::before { display: none; }
            @page { margin: 2.5cm; }
        }
    </style>
</head>
<body>

    <!-- WebGL Background -->
    <canvas id="webgl-canvas"></canvas>

    <!-- Global Header -->
    <header class="py-4 px-8 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-gradient-to-br from-sky-400 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-[0_0_15px_rgba(14,165,233,0.5)]">
                N
            </div>
            <span class="font-bold tracking-widest text-lg text-white">NEMESIS</span>
        </div>
        
        <nav class="hidden md:flex items-center gap-8">
            <a href="/" class="nav-link">HOME</a>
            <a href="/index.html" class="nav-link">NEMESIS TRACER</a>
            <a href="/nemesis_id.html" class="nav-link">NEMESIS ID</a>
            <a href="/recovery_framework.html" class="nav-link text-sky-400">RECOVERY FRAMEWORK</a>
        </nav>
    </header>

    <div class="app-container">
        <!-- Sidebar Navigation -->
        <aside id="sidebar" class="custom-scrollbar">
            <div class="sidebar-header">
                <div class="text-center font-black text-slate-300 tracking-widest uppercase text-xs border-slate-700 pt-3">Intelligence Network</div>
            </div>

            <div class="nav-menu">
                <div class="nav-group-title">Master Overview</div>
                <a class="nav-item active" onclick="switchView('overview')"><i class="ph-bold ph-strategy text-lg"></i> Recovery Framework</a>
                <a class="nav-item" onclick="switchView('file-structure')"><i class="ph-bold ph-folders text-lg"></i> Case File Architecture</a>

                <div class="nav-group-title">The 12 Phases</div>
                <a class="nav-item" onclick="switchView('phase-1')"><i class="ph-bold ph-number-circle-one text-lg"></i> Incident Response</a>
                <a class="nav-item" onclick="switchView('phase-2')"><i class="ph-bold ph-number-circle-two text-lg"></i> Evidence Preservation</a>
                <a class="nav-item" onclick="switchView('phase-3')"><i class="ph-bold ph-number-circle-three text-lg"></i> Blockchain Forensics</a>
                <a class="nav-item" onclick="switchView('phase-4')"><i class="ph-bold ph-number-circle-four text-lg"></i> Intelligence Collection</a>
                <a class="nav-item" onclick="switchView('phase-5')"><i class="ph-bold ph-number-circle-five text-lg"></i> Entity Attribution</a>
                <a class="nav-item" onclick="switchView('phase-6')"><i class="ph-bold ph-number-circle-six text-lg"></i> Legal Case Building</a>
                <a class="nav-item" onclick="switchView('phase-7')"><i class="ph-bold ph-number-circle-seven text-lg"></i> Reporting</a>
                <a class="nav-item" onclick="switchView('phase-8')"><i class="ph-bold ph-number-circle-eight text-lg"></i> Exchange Notification</a>
                <a class="nav-item" onclick="switchView('phase-9')"><i class="ph-bold ph-number-circle-nine text-lg"></i> Civil Litigation</a>
                <a class="nav-item" onclick="switchView('phase-10')"><i class="ph-bold ph-number-circle-zero text-lg"></i> Criminal Investigation</a>
                <a class="nav-item" onclick="switchView('phase-11')"><i class="ph-bold ph-gavel text-lg"></i> Court Orders</a>
                <a class="nav-item" onclick="switchView('phase-12')"><i class="ph-bold ph-vault text-lg"></i> Asset Restitution</a>

                <div class="nav-group-title">Evidentiary Templates</div>
                <a class="nav-item" onclick="switchView('doc-incident')"><i class="ph-bold ph-file-text text-lg"></i> T-1: Incident Report</a>
                <a class="nav-item" onclick="switchView('doc-custody')"><i class="ph-bold ph-link text-lg"></i> T-2: Chain of Custody</a>
                <a class="nav-item" onclick="switchView('doc-expert')"><i class="ph-bold ph-scales text-lg"></i> T-3: Expert Witness Decl.</a>
                <a class="nav-item" onclick="switchView('doc-subpoena')"><i class="ph-bold ph-file-search text-lg"></i> T-4: Preservation Request</a>
                <a class="nav-item" onclick="switchView('doc-report')"><i class="ph-bold ph-file-pdf text-lg"></i> T-5: Master Forensic Report</a>
            </div>
        </aside>

        <!-- Main Content Area -->
        <main id="main-content" class="custom-scrollbar">

            <!-- OVERVIEW -->
            <section id="overview" class="content-section active">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LIONSGATE NETWORK</div>
                    <h1>Cryptocurrency Asset Recovery Framework</h1>
                    <p>The complete, 12-phase lifecycle for responding to, investigating, and litigating digital asset theft. This framework bridges the gap between raw blockchain forensics and actionable legal outcomes required for asset restitution.</p>
                </div>
            </section>

            <!-- FILE STRUCTURE -->
            <section id="file-structure" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">CONFIDENTIAL</div>
                    <h1>Master Case File Architecture</h1>
                    <p>Standardized directory structure for maintaining evidentiary integrity during digital asset litigation.</p>
                </div>
            </section>

            <!-- PHASE 1 -->
            <section id="phase-1" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LIONSGATE</div>
                    <h1>Phase 1: Incident Response</h1>
                    <p>Immediately executed upon discovery of the theft or unauthorized transfer. The critical window for asset recovery is the first 48 hours.</p>
                    <h2>Objectives</h2>
                    <ul>
                        <li>Preserve digital evidence in its original state.</li>
                        <li>Prevent further losses (revoke smart contract approvals).</li>
                        <li>Begin strict chain of custody documentation.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 2 -->
            <section id="phase-2" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LIONSGATE</div>
                    <h1>Phase 2: Evidence Preservation</h1>
                    <p>The systematic capture of volatile digital evidence to ensure admissibility in future legal proceedings under Daubert standards.</p>
                    <h2>Objectives</h2>
                    <ul>
                        <li>Capture web browser artifacts, extensions (e.g., MetaMask logs), and device memory.</li>
                        <li>Document communication with malicious actors (phishing emails, Telegram logs).</li>
                        <li>Cryptographically hash (SHA-256) all collected files for integrity verification.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 3 -->
            <section id="phase-3" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">FORENSICS</div>
                    <h1>Phase 3: Blockchain Forensics</h1>
                    <p>This is where the <strong>NEMESIS OS</strong> is deployed to reconstruct the exact cryptographic path of stolen assets.</p>
                    <h2>Analysis Performed by NEMESIS</h2>
                    <ul>
                        <li>Wallet clustering (Common Input Ownership Heuristics)</li>
                        <li>Cross-chain tracing via Asset Continuity Scoring (ACS)</li>
                        <li>De-obfuscation of Mixer / Tornado Cash deposits</li>
                    </ul>
                </div>
            </section>
            
            <!-- PHASE 4 -->
            <section id="phase-4" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">INTELLIGENCE</div>
                    <h1>Phase 4: Intelligence Collection (OSINT)</h1>
                    <p>Fusing raw blockchain addresses with real-world intelligence to de-anonymize the threat actor.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Scraping darknet forums and ransomware leak sites for address mentions.</li>
                        <li>Analyzing GitHub, Telegram, and Discord for developer slip-ups.</li>
                        <li>Deploying NEMESIS Entity Resolution to cross-reference known attacker profiles.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 5 -->
            <section id="phase-5" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">ATTRIBUTION</div>
                    <h1>Phase 5: Entity Attribution</h1>
                    <p>The process of formally linking the cryptographic movement of funds to a distinct, actionable real-world entity or service provider.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Identifying the terminal Centralized Exchange (CEX) where funds were deposited (e.g., Binance, Kraken).</li>
                        <li>Determining the jurisdictional location of the holding entity.</li>
                        <li>Drafting the Entity Attribution Assessment report.</li>
                    </ul>
                </div>
            </section>
            
            <!-- PHASE 6 -->
            <section id="phase-6" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LEGAL</div>
                    <h1>Phase 6: Legal Case Building</h1>
                    <p>Translating technical forensic findings into legally actionable documents for attorneys and judges.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Drafting Expert Witness Declarations explaining the blockchain tracing.</li>
                        <li>Preparing the civil complaint or law enforcement referral packet.</li>
                        <li>Compiling all exhibits into a court-ready master file.</li>
                    </ul>
                </div>
            </section>
            
            <!-- PHASE 7 -->
            <section id="phase-7" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">REPORTING</div>
                    <h1>Phase 7: Reporting</h1>
                    <p>The formal delivery of the Master Forensic Trace Report to the client and legal counsel.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Final review of tracing accuracy and confidence scores.</li>
                        <li>Delivery of interactive graphs and raw CSV ledgers.</li>
                        <li>Briefing the legal team on the technical mechanics of the theft.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 8 -->
            <section id="phase-8" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">ACTION</div>
                    <h1>Phase 8: Exchange Notification</h1>
                    <p>Serving Preservation Requests to the identified Centralized Exchanges to prevent the dissipation of funds.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Issuing formal legal hold requests to the exchange's legal department.</li>
                        <li>Providing the exchange with the exact deposit hashes and timestamps.</li>
                        <li>Requesting preservation of KYC/AML records and login IPs.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 9 -->
            <section id="phase-9" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LITIGATION</div>
                    <h1>Phase 9: Civil Litigation</h1>
                    <p>Initiating formal legal proceedings against "John Doe" defendants or identified actors in civil court to recover damages.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Filing the civil complaint.</li>
                        <li>Filing motions for alternative service (e.g., serving via NFT drop to the attacker's wallet).</li>
                        <li>Seeking damages for conversion and unjust enrichment.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 10 -->
            <section id="phase-10" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">ENFORCEMENT</div>
                    <h1>Phase 10: Criminal Investigation</h1>
                    <p>Escalating the case file to federal authorities (FBI, Secret Service, DOJ) for parallel criminal proceedings.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Submitting the compiled evidence packet to the IC3.</li>
                        <li>Direct liaison with Cyber Task Force agents.</li>
                        <li>Assisting law enforcement with grand jury subpoenas for exchange records.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 11 -->
            <section id="phase-11" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">COURT ORDER</div>
                    <h1>Phase 11: Court Orders</h1>
                    <p>Obtaining judicial orders compelling the exchange to freeze the assets and unmask the identity of the account holder.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Executing Norwich Pharmacal Orders (NPO) or US equivalents.</li>
                        <li>Executing Temporary Restraining Orders (TRO) and Injunctions.</li>
                        <li>Analyzing the returned KYC data to identify the perpetrator.</li>
                    </ul>
                </div>
            </section>

            <!-- PHASE 12 -->
            <section id="phase-12" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">RESTITUTION</div>
                    <h1>Phase 12: Asset Restitution</h1>
                    <p>The final seizure and repatriation of stolen assets back to the victim.</p>
                    <h2>Key Actions</h2>
                    <ul>
                        <li>Coordinating with the exchange to execute the final turnover order.</li>
                        <li>Receiving the funds into a secure, cold-storage escrow facility.</li>
                        <li>Final disbursement to the victim and case closure.</li>
                    </ul>
                </div>
            </section>

            <!-- T-1: Incident Report -->
            <section id="doc-incident" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">EVIDENCE</div>
                    <h1>T-1: Initial Incident Report</h1>
                    <p><strong>Date Prepared:</strong> [DATE]</p>
                    <p><strong>Victim Name:</strong> [NAME]</p>
                    <p><strong>Nature of Incident:</strong> Unauthorized Access / Smart Contract Exploit</p>
                    <h3>Summary of Events</h3>
                    <p>On [DATE] at approximately [TIME], the victim noticed an unauthorized transfer of [AMOUNT] [ASSET] from wallet address [ADDRESS]. The transaction hash is [HASH]. The victim had previously interacted with a malicious phishing site located at [URL].</p>
                    <h3>Immediate Actions Taken</h3>
                    <p>Revoked all token approvals via Etherscan. Transferred remaining funds to cold storage. Initiated NEMESIS forensic trace.</p>
                </div>
            </section>

            <!-- T-2: Chain of Custody -->
            <section id="doc-custody" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">EVIDENCE</div>
                    <h1>T-2: Chain of Custody Log</h1>
                    <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                        <tr style="background:#f1f5f9; border:1px solid #cbd5e1;">
                            <th style="padding:10px; text-align:left; border:1px solid #cbd5e1;">Item Description</th>
                            <th style="padding:10px; text-align:left; border:1px solid #cbd5e1;">Hash (SHA-256)</th>
                            <th style="padding:10px; text-align:left; border:1px solid #cbd5e1;">Date/Time Collected</th>
                            <th style="padding:10px; text-align:left; border:1px solid #cbd5e1;">Collected By</th>
                        </tr>
                        <tr>
                            <td style="padding:10px; border:1px solid #cbd5e1;">Forensic Image of Victim's iPhone</td>
                            <td style="padding:10px; border:1px solid #cbd5e1; font-family:monospace;">8a9b...f3c2</td>
                            <td style="padding:10px; border:1px solid #cbd5e1;">[DATE/TIME]</td>
                            <td style="padding:10px; border:1px solid #cbd5e1;">[ANALYST]</td>
                        </tr>
                        <tr>
                            <td style="padding:10px; border:1px solid #cbd5e1;">Exported MetaMask Logs (.json)</td>
                            <td style="padding:10px; border:1px solid #cbd5e1; font-family:monospace;">1d4e...9a7b</td>
                            <td style="padding:10px; border:1px solid #cbd5e1;">[DATE/TIME]</td>
                            <td style="padding:10px; border:1px solid #cbd5e1;">[ANALYST]</td>
                        </tr>
                    </table>
                </div>
            </section>
            
            <!-- T-3: Expert Witness Decl. -->
            <section id="doc-expert" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">EVIDENCE</div>
                    <h1>T-3: Expert Witness Declaration</h1>
                    <p>I, <strong>[EXPERT NAME]</strong>, declare under penalty of perjury as follows: I am a Blockchain Intelligence Analyst and Cyber-Forensics Investigator currently employed by Lionsgate Intelligence Network.</p>
                    <p>To trace the flow of funds, I utilized the NEMESIS Omni-Chain Intelligence Framework. Through behavioral clustering, I successfully traced the stolen assets through intermediary wallets to a custodial exchange, Binance. A freezing order is necessary to prevent dissipation.</p>
                </div>
            </section>

            <!-- T-4: Preservation Request -->
            <section id="doc-subpoena" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">LEGAL</div>
                    <h1>T-4: Preservation Request</h1>
                    <p><strong>To:</strong> [EXCHANGE NAME] Legal & Compliance Department</p>
                    <p>This letter serves as a formal demand that [EXCHANGE NAME] immediately take all necessary steps to freeze the accounts associated with the illicit deposits and preserve all related data and records (KYC, IPs, Ledgers) in anticipation of a forthcoming court order.</p>
                </div>
            </section>

            <!-- T-5: Master Forensic Report -->
            <section id="doc-report" class="content-section">
                <div class="print-actions"><button class="btn-print" onclick="window.print()"><i class="ph-bold ph-printer"></i> Export PDF</button></div>
                <div class="legal-document">
                    <div class="watermark">CONFIDENTIAL</div>
                    <h1>T-5: Master Forensic Trace Report</h1>
                    <p>This report details the forensic tracing of digital assets associated with Case [CASE NUMBER]. Utilizing the NEMESIS Autonomous Intelligence Framework, analysts have successfully mapped the lifecycle of the compromised assets from the origin seed address through various obfuscation layers.</p>
                    <div style="background:#f8fafc; padding:20px; border:1px solid #e2e8f0; border-radius:8px; margin-top:20px; font-family:'Inter', sans-serif;">
                        <div style="font-size:1.5rem; font-weight:900; color:#059669; margin-bottom:10px;">RECOVERY PROBABILITY: HIGH (85%)</div>
                        <strong>Total Loss Assessed:</strong> $150,000 USD<br>
                        <strong>Identified Custodial Terminals:</strong> Binance Holdings Ltd., Kraken
                    </div>
                </div>
            </section>

        </main>
    </div>

    <script>
        function switchView(viewId) {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            const activeNav = document.querySelector(`a[onclick="switchView('${viewId}')"]`);
            if(activeNav) activeNav.classList.add('active');

            document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
            document.getElementById(viewId).classList.add('active');
        }

        // --- WebGL Background (Subtle Network Effect) ---
        function initWebGL() {
            const canvas = document.getElementById('webgl-canvas');
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            
            renderer.setSize(window.innerWidth, window.innerHeight);
            canvas.appendChild(renderer.domElement);

            const geometry = new THREE.BufferGeometry();
            const particles = 400;
            const positions = new Float32Array(particles * 3);

            for (let i = 0; i < particles * 3; i++) {
                positions[i] = (Math.random() - 0.5) * 20;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            const material = new THREE.PointsMaterial({ 
                color: 0x38bdf8,
                size: 0.05,
                transparent: true,
                opacity: 0.5
            });

            const points = new THREE.Points(geometry, material);
            scene.add(points);
            camera.position.z = 5;

            function animate() {
                requestAnimationFrame(animate);
                points.rotation.y += 0.0005;
                points.rotation.x += 0.0002;
                renderer.render(scene, camera);
            }
            animate();

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
        }

        window.addEventListener('DOMContentLoaded', initWebGL);
    </script>
</body>
</html>
"""

with open(r"c:\Users\LEGIONX\Downloads\cases\templates\recovery_framework.html", "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)
