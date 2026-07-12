import re
import os

filepath = "templates/nemesis_tracer.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Seed Input Label and Placeholder
content = re.sub(
    r'<label class="block text-slate-500 text-\[10px\] font-bold uppercase tracking-widest mb-2">Target Seed Wallets / Suspects</label>',
    r'<label class="block text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-2 flex justify-between items-center"><span>Target Seed Wallets / Suspects / TxHash</span><span id="tx-detect-badge" class="hidden px-2 py-0.5 rounded text-[8px] bg-blue-100 text-blue-600 border border-blue-200"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Analyzing Tx...</span></label>',
    content
)

content = re.sub(
    r'placeholder="Auto-populated or Enter 0x... addresses \(one per line\)"',
    r'placeholder="Enter Wallet Addresses or Transaction Hash (TxID) to Auto-Detect..." onblur="analyzeSeedInput(this.value)"',
    content
)

# 2. Network Icons Mapping
network_options = [
    ("ALL", "🌐", "ALL SUPPORTED NETWORKS", ""),
    ("ETH", "https://cryptologos.cc/logos/ethereum-eth-logo.svg", "Ethereum (ETH)", ""),
    ("BSC", "https://cryptologos.cc/logos/bnb-bnb-logo.svg", "Binance Smart Chain", ""),
    ("POLYGON", "https://cryptologos.cc/logos/polygon-matic-logo.svg", "Polygon (MATIC)", ""),
    ("ARBITRUM", "https://cryptologos.cc/logos/arbitrum-arb-logo.svg", "Arbitrum (ARB)", ""),
    ("OPTIMISM", "https://cryptologos.cc/logos/optimism-ethereum-op-logo.svg", "Optimism (OP)", ""),
    ("BASE", "https://logowik.com/content/uploads/images/base-coin8494.logowik.com.webp", "Base", ""),
    ("SOL", "https://cryptologos.cc/logos/solana-sol-logo.svg", "Solana (SOL)", ""),
    ("BTC", "https://cryptologos.cc/logos/bitcoin-btc-logo.svg", "Bitcoin (BTC)", ""),
    ("TRX", "https://cryptologos.cc/logos/tron-trx-logo.svg", "Tron (TRX)", ""),
    ("XRP", "https://cryptologos.cc/logos/xrp-xrp-logo.svg", "Ripple (XRP)", ""),
    ("AVAX", "https://cryptologos.cc/logos/avalanche-avax-logo.svg", "Avalanche (AVAX)", ""),
]

# Currency Icons Mapping
currency_options = [
    ("USD", "💵", "USD"),
    ("ETH", "https://cryptologos.cc/logos/ethereum-eth-logo.svg", "ETH"),
    ("BTC", "https://cryptologos.cc/logos/bitcoin-btc-logo.svg", "BTC"),
    ("USDT", "https://cryptologos.cc/logos/tether-usdt-logo.svg", "USDT"),
    ("USDC", "https://cryptologos.cc/logos/usd-coin-usdc-logo.svg", "USDC"),
]

def generate_custom_dropdown(options, id_prefix, width_class="w-full", is_currency=False):
    html = f'''
    <div class="relative {width_class}" id="{id_prefix}-container">
        <!-- Hidden input to store value -->
        <input type="hidden" id="{id_prefix}" value="{options[0][0]}">
        
        <!-- Dropdown Button -->
        <button type="button" onclick="toggleDropdown('{id_prefix}-dropdown')" class="flex items-center justify-between w-full bg-white/80 border border-slate-200/40 { 'rounded-l-lg border-r-0' if is_currency else 'rounded-lg' } p-3 text-[11px] text-slate-700 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 transition shadow-sm h-full min-h-[46px]">
            <div class="flex items-center gap-2" id="{id_prefix}-selected">
                {f'<img src="{options[0][1]}" class="w-4 h-4 object-contain">' if options[0][1].startswith('http') else f'<span class="text-sm">{options[0][1]}</span>'}
                <span>{options[0][2]}</span>
            </div>
            <i class="fa-solid fa-chevron-down text-slate-400"></i>
        </button>

        <!-- Dropdown Menu -->
        <div id="{id_prefix}-dropdown" class="hidden absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-60 overflow-y-auto">
    '''
    
    for val, icon, text, _ in options:
        icon_html = f'<img src="{icon}" class="w-4 h-4 object-contain">' if icon.startswith('http') else f'<span class="text-sm w-4 text-center">{icon}</span>'
        html += f'''
            <button type="button" onclick="selectDropdownOption('{id_prefix}', '{val}', '{icon}', '{text}')" class="flex items-center gap-2 w-full text-left px-4 py-2 text-[11px] font-bold text-slate-700 hover:bg-slate-50 transition">
                {icon_html}
                <span>{text}</span>
            </button>
        '''
    html += '''
        </div>
    </div>
    '''
    return html

currency_html = generate_custom_dropdown(currency_options, "landing-target-currency", "w-1/3", is_currency=True)
network_html = generate_custom_dropdown(network_options, "landing-chain-select", "w-full", is_currency=False)

# Replace Currency Select
content = re.sub(
    r'<select id="landing-target-currency".*?</select>',
    currency_html,
    content,
    flags=re.DOTALL
)

# Replace Network Select
content = re.sub(
    r'<select id="landing-chain-select".*?</select>',
    network_html,
    content,
    flags=re.DOTALL
)

# Inject JS for custom dropdowns and TxHash analysis
js_injection = '''
<script>
    function toggleDropdown(id) {
        const dropdown = document.getElementById(id);
        const allDropdowns = document.querySelectorAll('[id$="-dropdown"]');
        allDropdowns.forEach(d => { if(d.id !== id) d.classList.add('hidden'); });
        dropdown.classList.toggle('hidden');
    }

    function selectDropdownOption(prefix, value, icon, text) {
        document.getElementById(prefix).value = value;
        const iconHtml = icon.startsWith('http') ? `<img src="${icon}" class="w-4 h-4 object-contain">` : `<span class="text-sm">${icon}</span>`;
        document.getElementById(`${prefix}-selected`).innerHTML = `${iconHtml}<span>${text}</span>`;
        document.getElementById(`${prefix}-dropdown`).classList.add('hidden');
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('[id$="-container"]')) {
            document.querySelectorAll('[id$="-dropdown"]').forEach(d => d.classList.add('hidden'));
        }
    });

    async function analyzeSeedInput(val) {
        const value = val.trim();
        // Basic TxHash heuristics: 64 hex chars (EVM/BTC), Solana (88 base58 chars), Tron (64 hex)
        const isTxHash = /^(0x)?[a-fA-F0-9]{64}$/.test(value) || /^[1-9A-HJ-NP-Za-km-z]{88}$/.test(value);
        
        if (!isTxHash) return; // Ignore standard addresses

        const badge = document.getElementById('tx-detect-badge');
        badge.classList.remove('hidden');

        try {
            const response = await fetch('/api/tracer/analyze-input', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: value })
            });
            const data = await response.json();
            
            if (data.success) {
                // Auto-fill fields
                if (data.target_address) {
                    document.getElementById('landing-seed-input').value = data.target_address;
                }
                if (data.total_loss) {
                    document.getElementById('landing-target-amount').value = data.total_loss;
                }
                if (data.currency) {
                    // Quick map hack to select currency
                    const currMap = {"USD":"💵", "ETH":"https://cryptologos.cc/logos/ethereum-eth-logo.svg", "BTC":"https://cryptologos.cc/logos/bitcoin-btc-logo.svg", "USDC":"https://cryptologos.cc/logos/usd-coin-usdc-logo.svg", "USDT":"https://cryptologos.cc/logos/tether-usdt-logo.svg"};
                    if (currMap[data.currency]) {
                        selectDropdownOption('landing-target-currency', data.currency, currMap[data.currency], data.currency);
                    }
                }
                if (data.network) {
                    const netMap = {
                        "ETH": ["https://cryptologos.cc/logos/ethereum-eth-logo.svg", "Ethereum (ETH)"],
                        "BTC": ["https://cryptologos.cc/logos/bitcoin-btc-logo.svg", "Bitcoin (BTC)"],
                        "BSC": ["https://cryptologos.cc/logos/bnb-bnb-logo.svg", "Binance Smart Chain"],
                        "POLYGON": ["https://cryptologos.cc/logos/polygon-matic-logo.svg", "Polygon (MATIC)"],
                        "TRX": ["https://cryptologos.cc/logos/tron-trx-logo.svg", "Tron (TRX)"],
                        "SOL": ["https://cryptologos.cc/logos/solana-sol-logo.svg", "Solana (SOL)"]
                    };
                    const net = data.network.toUpperCase();
                    if (netMap[net]) {
                        selectDropdownOption('landing-chain-select', net, netMap[net][0], netMap[net][1]);
                    }
                }
                
                // Add a success toast/indicator
                badge.innerHTML = '<i class="fa-solid fa-check mr-1"></i> Tx Decoded!';
                badge.classList.replace('text-blue-600', 'text-green-600');
                badge.classList.replace('bg-blue-100', 'bg-green-100');
                badge.classList.replace('border-blue-200', 'border-green-200');
                setTimeout(() => badge.classList.add('hidden'), 3000);
            } else {
                badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation mr-1"></i> Failed to decode';
                badge.classList.replace('text-blue-600', 'text-red-600');
                badge.classList.replace('bg-blue-100', 'bg-red-100');
                badge.classList.replace('border-blue-200', 'border-red-200');
                setTimeout(() => badge.classList.add('hidden'), 3000);
            }
        } catch (e) {
            console.error(e);
            badge.classList.add('hidden');
        }
    }
</script>
'''

# Inject script before </body>
content = content.replace("</body>", js_injection + "\n</body>")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated nemesis_tracer.html UI components!")
