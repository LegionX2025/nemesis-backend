// nemesis-ui.js
// Global Nemesis Pro UI framework

document.addEventListener('DOMContentLoaded', () => {
    injectGlobalNavigation();
    injectWatermark();
});

function injectGlobalNavigation() {
    const headerHtml = `
        <header class="nemesis-header-light w-full py-4 px-8 flex justify-between items-center shadow-sm">
            <div class="flex items-center gap-4">
                <img src="logo_nemesis.jpeg" alt="Nemesis Logo" class="h-10 w-10 rounded-full shadow-md object-cover border-2 border-white">
                <h1 class="text-2xl font-black tracking-widest text-slate-800 uppercase flex items-center gap-2">
                    Lionsgate <span class="text-blue-600">Nemesis Pro</span>
                </h1>
            </div>
            <nav class="flex gap-6 font-bold text-sm tracking-wide text-slate-600">
                <a href="/" class="hover:text-blue-600 transition">HOME</a>
                <a href="/about" class="hover:text-blue-600 transition">ABOUT</a>
                <a href="/tracer" class="hover:text-blue-600 transition">TRACER</a>
                <a href="/nemesis_id" class="hover:text-blue-600 transition">NEMESIS ID</a>
                <a href="/api_docs" class="hover:text-blue-600 transition">API DOCS</a>
                <a href="/admin" class="hover:text-blue-600 transition">ADMIN</a>
            </nav>
        </header>
    `;

    const footerHtml = `
        <footer class="nemesis-footer-light mt-auto bg-slate-50 border-t border-slate-200 py-6 px-8 relative z-50">
            <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
                <div class="text-left">
                    <p class="font-black text-slate-800 tracking-widest uppercase">Lionsgate Intelligence Network</p>
                    <p class="text-[10px] font-mono text-slate-500 mt-1 uppercase tracking-widest">NEMESIS™ &copy; 2026. Restricted Use Only.</p>
                </div>
                <div class="flex flex-wrap gap-6 text-[11px] font-bold tracking-widest text-slate-600 uppercase">
                    <a href="#" class="hover:text-blue-600 transition" onclick="alert('NEMESIS™ END USER LICENSE AGREEMENT (EULA)...')">Terms of Service</a>
                    <a href="#" class="hover:text-blue-600 transition">Privacy</a>
                    <a href="/about" class="hover:text-blue-600 transition">About</a>
                    <a href="/api_docs" class="text-blue-600 hover:text-indigo-600 transition flex items-center gap-1"><i class="fa-solid fa-code"></i> API Documentations</a>
                </div>
                <div class="flex gap-4 text-slate-400">
                    <a href="#" class="hover:text-blue-600 transition"><i class="fa-brands fa-twitter"></i></a>
                    <a href="#" class="hover:text-blue-600 transition"><i class="fa-brands fa-github"></i></a>
                    <a href="#" class="hover:text-blue-600 transition"><i class="fa-solid fa-envelope"></i></a>
                </div>
            </div>
        </footer>
    `;

    // Only inject if there isn't already a custom header
    if (!document.querySelector('header.custom-header')) {
        document.body.insertAdjacentHTML('afterbegin', headerHtml);
        document.body.insertAdjacentHTML('beforeend', footerHtml);
    }
}

function injectWatermark() {
    const watermark = document.createElement('div');
    watermark.className = 'nemesis-watermark';
    document.body.appendChild(watermark);
}

// Global Wallet Resolver with Official Colored Icons
window.NemesisResolver = {
    getChainIcon: function(chain) {
        const chains = {
            'ETHEREUM': 'https://cryptologos.cc/logos/ethereum-eth-logo.png',
            'BITCOIN': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
            'SOLANA': 'https://cryptologos.cc/logos/solana-sol-logo.png',
            'POLYGON': 'https://cryptologos.cc/logos/polygon-matic-logo.png',
            'TRON': 'https://cryptologos.cc/logos/tron-trx-logo.png',
            'BSC': 'https://cryptologos.cc/logos/bnb-bnb-logo.png',
            'XRP': 'https://cryptologos.cc/logos/xrp-xrp-logo.png'
        };
        return chains[chain.toUpperCase()] || 'https://cryptologos.cc/logos/ethereum-eth-logo.png';
    },
    getAssetIcon: function(asset) {
        const assets = {
            'USDT': 'https://cryptologos.cc/logos/tether-usdt-logo.png',
            'USDC': 'https://cryptologos.cc/logos/usd-coin-usdc-logo.png',
            'DAI': 'https://cryptologos.cc/logos/multi-collateral-dai-dai-logo.png',
            'ETH': 'https://cryptologos.cc/logos/ethereum-eth-logo.png',
            'BTC': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
            'WETH': 'https://cryptologos.cc/logos/ethereum-eth-logo.png'
        };
        return assets[asset.toUpperCase()] || 'https://cryptologos.cc/logos/ethereum-eth-logo.png'; /* Default generic */
    },
    formatAddress: function(address, chain = 'ETHEREUM', label = null) {
        const icon = this.getChainIcon(chain);
        const shortAddr = address.substring(0,6) + '...' + address.substring(address.length-4);
        const labelHtml = label ? `<span class="ml-2 bg-blue-100 text-blue-800 text-[10px] px-2 py-0.5 rounded-full font-bold">${label}</span>` : '';
        
        return `
            <div class="flex items-center gap-2 font-mono text-sm">
                <img src="${icon}" class="network-icon" alt="${chain}">
                <span class="text-slate-700 hover:text-blue-600 cursor-pointer transition">${shortAddr}</span>
                ${labelHtml}
            </div>
        `;
    },
    formatAsset: function(amount, symbol) {
        const icon = this.getAssetIcon(symbol);
        const amtStr = parseFloat(amount).toLocaleString(undefined, {maximumFractionDigits: 4});
        return `
            <div class="flex items-center gap-2 font-bold text-slate-800">
                <img src="${icon}" class="asset-icon" alt="${symbol}">
                <span>${amtStr} <span class="text-slate-500 text-xs">${symbol}</span></span>
            </div>
        `;
    }
};
// NEMESIS UNIFIED INTELLIGENCE - Auto-Heal Observer
document.addEventListener('DOMContentLoaded', () => {
    const modalHtml = 
        <div id="nemesis-auto-heal-modal">
            <div class="nemesis-heal-spinner"></div>
            <h2>⚠️ SYSTEM ANOMALY DETECTED</h2>
            <p>Autonomous AI Healing in Progress. Please wait while the system regenerates and redeploys code...</p>
        </div>
    ;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Global fetch interceptor to catch 500s or 503s
    const originalFetch = window.fetch;
    window.fetch = async function() {
        try {
            const response = await originalFetch.apply(this, arguments);
            if (response.status >= 500) {
                document.getElementById('nemesis-auto-heal-modal').classList.add('active');
                // Poll for recovery
                checkRecovery();
            }
            return response;
        } catch (error) {
            document.getElementById('nemesis-auto-heal-modal').classList.add('active');
            checkRecovery();
            throw error;
        }
    };

    function checkRecovery() {
        const interval = setInterval(async () => {
            try {
                const res = await originalFetch('/health');
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'ok') {
                        document.getElementById('nemesis-auto-heal-modal').classList.remove('active');
                        clearInterval(interval);
                        // Reload state seamlessly
                        window.location.reload();
                    }
                }
            } catch (e) {
                // Still down
            }
        }, 5000);
    }
});
