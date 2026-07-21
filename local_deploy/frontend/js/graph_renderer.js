/**
 * NEMESIS Graph Renderer - Cytoscape Migration (Design 1)
 */

const LOGO_MAP = {
    'binance': 'https://cryptologos.cc/logos/binance-coin-bnb-logo.png',
    'uniswap': 'https://cryptologos.cc/logos/uniswap-uni-logo.png',
    'tether': 'https://cryptologos.cc/logos/tether-usdt-logo.png',
    'bitcoin': 'https://cryptologos.cc/logos/bitcoin-btc-logo.png',
    'ethereum': 'https://cryptologos.cc/logos/ethereum-eth-logo.png',
    'kraken': 'https://cryptologos.cc/logos/kraken-btc-logo.png',
    'unknown': 'https://cdn-icons-png.flaticon.com/512/8552/8552821.png'
};

function getEntityLogo(entityName) {
    if (!entityName) return LOGO_MAP['unknown'];
    const lowerName = entityName.toLowerCase();
    for (const key in LOGO_MAP) {
        if (lowerName.includes(key)) return LOGO_MAP[key];
    }
    return LOGO_MAP['unknown'];
}

function formatCurrency(amount) {
    if (!amount) return "$0.00";
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

class NemesisGraph {
    constructor(containerId) {
        this.containerId = containerId;
        this.network = null;
    }

    render(transactions) {
        const elements = [];
        const nodeSet = new Set();

        transactions.forEach(tx => {
            // Source Node
            if (!nodeSet.has(tx.from_address)) {
                let shortAddr = tx.from_address.length > 15 ? tx.from_address.substring(0,6) + '...' + tx.from_address.substring(tx.from_address.length - 4) : tx.from_address;
                elements.push({
                    data: {
                        id: tx.from_address,
                        label: (tx.from_entity || 'UNKNOWN') + '\\n' + shortAddr,
                        color: tx.from_entity ? '#3b82f6' : '#94a3b8',
                        image: getEntityLogo(tx.from_entity)
                    }
                });
                nodeSet.add(tx.from_address);
            }

            // Target Node
            if (!nodeSet.has(tx.to_address)) {
                let shortAddr = tx.to_address.length > 15 ? tx.to_address.substring(0,6) + '...' + tx.to_address.substring(tx.to_address.length - 4) : tx.to_address;
                elements.push({
                    data: {
                        id: tx.to_address,
                        label: (tx.to_entity || 'UNKNOWN') + '\\n' + shortAddr,
                        color: tx.to_entity ? '#f97316' : '#94a3b8',
                        image: getEntityLogo(tx.to_entity)
                    },
                    classes: tx.to_entity ? 'target' : ''
                });
                nodeSet.add(tx.to_address);
            }

            // Edge
            elements.push({
                data: {
                    source: tx.from_address,
                    target: tx.to_address,
                    label: (tx.asset || 'ASSET') + '\\n' + formatCurrency(tx.value_usd || 0)
                },
                classes: 'animated'
            });
        });

        // Initialize using the global engine script
        if (typeof initNemesisGraph === 'function') {
            this.network = initNemesisGraph(this.containerId, elements, 'dark');
            
            // Re-bind click event for legacy compatibility
            this.network.on('tap', 'node', function(evt){
                const node = evt.target;
                if(window.openDossier) window.openDossier('graph_node', { id: node.id(), entity: node.data('label') });
            });
            this.network.on('tap', 'edge', function(evt){
                const edge = evt.target;
                if(window.openDossier) window.openDossier('graph_edge', { from: edge.data('source'), to: edge.data('target') });
            });
            this.network.on('cxttap', 'node', function(evt){
                // Right click
                if(window.openContextMenu) window.openContextMenu(evt.originalEvent, { id: evt.target.id() });
            });
            
        } else {
            console.error("Nemesis Graph Engine not loaded! Ensure nemesis_graph_engine.js is included.");
        }
    }
}
