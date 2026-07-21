document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    // 1. Inject Global CSS for Header and Footer
    const style = document.createElement('style');
    style.innerHTML = `
        /* CORPORATE INTELLIGENCE GLOBAL NAV (MODERN STYLE) */
        #nemesis-global-nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 70px;
            background: rgba(10, 15, 30, 0.90);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(59, 130, 246, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
            z-index: 999999;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
            font-family: 'Inter', sans-serif;
        }

        .nem-brand {
            display: flex; align-items: center; gap: 1rem; text-decoration: none;
        }

        .nem-brand img {
            height: 42px; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.5);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
            transition: transform 0.3s ease;
        }
        
        .nem-brand:hover img { transform: scale(1.05); box-shadow: 0 0 30px rgba(59, 130, 246, 0.6); }

        .nem-brand span {
            font-weight: 900; font-size: 1.4rem; color: #f8fafc; letter-spacing: 3px;
            text-shadow: 0 0 15px rgba(248, 250, 252, 0.2);
            text-transform: uppercase;
        }

        .nem-nav-links {
            display: flex; gap: 1.5rem; align-items: center; height: 100%;
        }

        .nem-link {
            color: #94a3b8; text-decoration: none; font-size: 0.8rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 1px; transition: all 0.3s ease;
            display: flex; align-items: center; gap: 0.5rem;
            height: 100%; position: relative; padding: 0 0.5rem;
        }

        .nem-link::after {
            content: ''; position: absolute; width: 0; height: 3px; bottom: 0; left: 0;
            background-color: #3b82f6; transition: width 0.3s ease;
            box-shadow: 0 0 12px #3b82f6;
        }

        .nem-link:hover::after, .nem-link.active::after { width: 100%; }
        .nem-link:hover, .nem-link.active { color: #60a5fa; text-shadow: 0 0 10px rgba(96, 165, 250, 0.5); }

        /* DROPDOWN MENU FOR APPS */
        .nem-dropdown-wrapper {
            position: relative; height: 100%; display: flex; align-items: center;
        }
        
        .nem-dropdown-trigger {
            cursor: pointer;
        }

        .nem-dropdown-menu {
            position: absolute; top: 70px; right: 0; width: 600px;
            background: rgba(10, 15, 30, 0.95);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-top: none;
            border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
            display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 1.5rem;
            opacity: 0; pointer-events: none; transform: translateY(-10px);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .nem-dropdown-wrapper:hover .nem-dropdown-menu {
            opacity: 1; pointer-events: auto; transform: translateY(0);
        }

        .nem-dropdown-item {
            display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem;
            border-radius: 8px; text-decoration: none; color: #cbd5e1;
            transition: background 0.2s, transform 0.2s;
            border: 1px solid transparent;
        }

        .nem-dropdown-item:hover {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            transform: translateX(5px);
            color: #fff;
        }

        .nem-dropdown-icon {
            width: 32px; height: 32px; border-radius: 6px; background: rgba(30, 41, 59, 0.8);
            display: flex; align-items: center; justify-content: center; color: #3b82f6;
            font-size: 1.1rem; border: 1px solid rgba(59, 130, 246, 0.2);
        }

        .nem-dropdown-text h4 { margin: 0; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; color: #f8fafc; }
        .nem-dropdown-text p { margin: 0; font-size: 0.65rem; color: #64748b; font-family: 'JetBrains Mono', monospace; margin-top: 2px;}

        /* GLOBAL FOOTER */
        #nemesis-global-footer {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: 40px;
            background: rgba(10, 15, 30, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid rgba(59, 130, 246, 0.3);
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 999999;
            color: #94a3b8;
            font-size: 0.7rem;
            font-family: 'JetBrains Mono', monospace;
            box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.5);
        }
        
        .footer-status { display: flex; align-items: center; gap: 0.75rem; color: #10b981; font-weight: bold; text-shadow: 0 0 8px rgba(16,185,129,0.5); letter-spacing: 1px;}
        .footer-dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981; animation: pulse 1.5s infinite alternate; }
        @keyframes pulse { from { opacity: 0.5; transform: scale(0.9); } to { opacity: 1; transform: scale(1.2); } }

        /* Layout adjustment for fixed headers */
        body { padding-top: 70px !important; padding-bottom: 40px !important; }
    `;
    document.head.appendChild(style);

    // 2. Build Apps List (Data)
    const apps = [
        { name: "NEMESIS ID", desc: "Omni-chain Entity Resolution", icon: "fa-fingerprint", link: "nemesis_id_landing.html" },
        { name: "NEMESIS Tracer", desc: "Quantum Flow Visualization", icon: "fa-project-diagram", link: "nemesis_tracer_landing.html" },
        { name: "Threat Hunter", desc: "Active Vector Detection", icon: "fa-spider", link: "nemesis_threat_hunter.html" },
        { name: "APEX Engine", desc: "Advanced Predictive Analytics", icon: "fa-rocket", link: "apex_landing.html" },
        { name: "Darknet Intel", desc: "Deep Web Corroboration", icon: "fa-user-secret", link: "darknet_search.html" },
        { name: "Master Audit", desc: "Smart Contract Vulnerability", icon: "fa-shield-halved", link: "audit.html" },
        { name: "Omega Core", desc: "AIL Autonomous Cluster", icon: "fa-brain", link: "nemesis_omega.html" },
        { name: "Command & Control", desc: "C2 Admin Server", icon: "fa-server", link: "admin.html" },
        { name: "API Reference", desc: "Developer Documentation", icon: "fa-book-atlas", link: "api_docs.html" },
        { name: "Recovery Framework", desc: "Legal & Subpoena Tools", icon: "fa-scale-balanced", link: "recovery_framework.html" }
    ];

    let dropdownHtml = '';
    apps.forEach(app => {
        dropdownHtml += `
            <a href="/${app.link}" class="nem-dropdown-item">
                <div class="nem-dropdown-icon"><i class="fa-solid ${app.icon}"></i></div>
                <div class="nem-dropdown-text">
                    <h4>${app.name}</h4>
                    <p>${app.desc}</p>
                </div>
            </a>
        `;
    });

    // 3. Inject Global Header
    const header = document.createElement('header');
    header.id = 'nemesis-global-nav';
    header.innerHTML = `
        <a href="/dashboard.html" class="nem-brand">
            <img src="/assets/butterfly_transparent.png" alt="NEMESIS Logo" onerror="this.src='butterfly_v3.png'">
            <span>NEMESIS</span>
        </a>
        <nav class="nem-nav-links">
            <a href="/dashboard.html" class="nem-link ${path.includes('dashboard') ? 'active' : ''}"><i class="fa-solid fa-house"></i> Home</a>
            <a href="/nemesis_tracer_landing.html" class="nem-link ${path.includes('tracer') ? 'active' : ''}"><i class="fa-solid fa-network-wired"></i> Tracer</a>
            <a href="/nemesis_id_landing.html" class="nem-link ${path.includes('nemesis_id') ? 'active' : ''}"><i class="fa-solid fa-id-card-clip"></i> Entity ID</a>
            
            <div class="nem-dropdown-wrapper">
                <div class="nem-link nem-dropdown-trigger"><i class="fa-solid fa-grid-2"></i> All Modules <i class="fa-solid fa-chevron-down text-[10px] ml-1"></i></div>
                <div class="nem-dropdown-menu">
                    ${dropdownHtml}
                </div>
            </div>
            <a href="/api_docs.html" class="nem-link"><i class="fa-solid fa-code"></i> Developer</a>
        </nav>
    `;
    document.body.prepend(header);

    // 4. Inject Global Footer
    const footer = document.createElement('footer');
    footer.id = 'nemesis-global-footer';
    footer.innerHTML = `
        <div class="footer-status">
            <div class="footer-dot"></div>
            NEMESIS OMNI-OS ONLINE | E2E ENCRYPTED
        </div>
        <div>&copy; 2026 LIONSGATE INTELLIGENCE NETWORK.</div>
        <div>KERNEL v5.2 | BUILD: OMEGA-X9</div>
    `;
    document.body.appendChild(footer);

    // Remove legacy local navs to prevent clash
    const oldNav = document.getElementById('global-nav');
    if (oldNav) oldNav.remove();
    const oldFooter = document.getElementById('global-footer');
    if (oldFooter) oldFooter.remove();
});
