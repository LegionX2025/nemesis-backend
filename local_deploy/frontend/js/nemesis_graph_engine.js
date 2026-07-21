/**
 * NEMESIS Omni-OS Graph Engine (Gradient Pill Nodes)
 * High-performance Cytoscape.js implementation with SVG Data URIs for pill nodes.
 */

function generatePillNodeSVG(label, role, balance, isDark) {
    const svgWidth = 260;
    const svgHeight = 180;
    
    // Main pill dimensions
    const pillWidth = 140;
    const pillHeight = 140;
    const pillX = (svgWidth - pillWidth) / 2;
    const pillY = 10; 
    
    let iconSvg = '';
    let roleText = (role || 'WALLET').toUpperCase();
    
    // Color definitions based on screenshot
    let strokeColor = '#3b82f6'; // Default Blue
    let glowColor = '#3b82f6';
    let iconColor = '#3b82f6';
    
    if (roleText.includes('BINANCE') || roleText.includes('COINBASE') || roleText.includes('EXCHANGE') || roleText.includes('CEX')) {
        strokeColor = '#0ea5e9'; // Light Blue
        glowColor = '#0ea5e9';
        iconColor = '#0ea5e9';
        iconSvg = `<circle cx="15" cy="15" r="12" fill="none" stroke="${iconColor}" stroke-width="3"/><path d="M18 10L12 15L18 20" stroke="${iconColor}" stroke-width="2" fill="none"/>`;
    } else if (roleText.includes('RANSOMWARE') || roleText.includes('SANCTIONED') || roleText.includes('MALICIOUS')) {
        strokeColor = '#ef4444'; // Red
        glowColor = '#ef4444';
        iconColor = '#ef4444';
        iconSvg = `<path d="M15 4C10 4 6 8 6 13C6 16 8 18 8 20V24H22V20C22 18 24 16 24 13C24 8 20 4 15 4ZM10 12C11.1 12 12 12.9 12 14C12 15.1 11.1 16 10 16C8.9 16 8 15.1 8 14C8 12.9 8.9 12 10 12ZM20 12C21.1 12 22 12.9 22 14C22 15.1 21.1 16 20 16C18.9 16 18 15.1 18 14C18 12.9 18.9 12 20 12Z" fill="${iconColor}"/>`;
    } else if (roleText.includes('MIXER') || roleText.includes('TORNADO')) {
        strokeColor = '#a855f7'; // Purple
        glowColor = '#a855f7';
        iconColor = '#a855f7';
        iconSvg = `<path d="M15 3C8.373 3 3 8.373 3 15C3 21.627 8.373 27 15 27C21.627 27 27 21.627 27 15C27 8.373 21.627 3 15 3ZM15 21C11.686 21 9 18.314 9 15C9 11.686 11.686 9 15 9C18.314 9 21 11.686 21 15C21 18.314 18.314 21 15 21Z" fill="${iconColor}"/>`;
    } else if (roleText.includes('TOKEN') || roleText.includes('USDT')) {
        strokeColor = '#22c55e'; // Green
        glowColor = '#22c55e';
        iconColor = '#22c55e';
        iconSvg = `<text x="5" y="22" font-family="Arial" font-size="20" font-weight="bold" fill="${iconColor}">T</text>`;
    } else if (roleText.includes('DEX') || roleText.includes('UNISWAP')) {
        strokeColor = '#ec4899'; // Pink
        glowColor = '#ec4899';
        iconColor = '#ec4899';
        iconSvg = `<path d="M15 3L25 15L15 27L5 15L15 3Z" fill="none" stroke="${iconColor}" stroke-width="3"/>`;
    } else {
        // Generic / Center Wallet
        strokeColor = '#3b82f6';
        glowColor = '#3b82f6';
        iconColor = '#3b82f6';
        iconSvg = `<rect x="2" y="6" width="26" height="18" rx="2" fill="none" stroke="${iconColor}" stroke-width="2"/><circle cx="20" cy="15" r="2" fill="${iconColor}"/>`;
    }

    const formatAmount = (bal) => {
        if (!bal) return "";
        if (typeof bal === 'string') return bal.startsWith('$') ? bal : "$" + bal;
        return "$" + parseFloat(bal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    };
    
    const formattedBalance = formatAmount(balance);
    const idLabel = label.length > 15 ? label.substring(0,6) + '...' + label.substring(label.length-4) : label;

    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="${svgWidth}" height="${svgHeight}">
            <defs>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="6" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            
            <g transform="translate(${pillX}, ${pillY})">
                <!-- Circular Icon Background -->
                <circle cx="70" cy="50" r="45" fill="#ffffff" stroke="${strokeColor}" stroke-width="2" filter="url(#glow)"/>
                
                <!-- Inner Icon -->
                <g transform="translate(55, 35)">
                    ${iconSvg}
                </g>

                <!-- Text Labels underneath the circle -->
                <!-- ID/Address -->
                <text x="70" y="115" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#0f172a" text-anchor="middle">${idLabel}</text>
                
                <!-- Role / Subtitle -->
                <text x="70" y="132" font-family="Arial, sans-serif" font-size="12" font-weight="900" fill="${strokeColor}" text-anchor="middle">${roleText}</text>
                
                <!-- Balance -->
                <text x="70" y="148" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#64748b" text-anchor="middle">${formattedBalance}</text>
            </g>
        </svg>
    `)}`;
}

function initNemesisGraph(containerId, elements, theme = 'light') {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Graph container '${containerId}' not found.`);
        return null;
    }

    if (theme === 'dark') {
        container.style.backgroundColor = '#020617';
        container.style.backgroundImage = 'radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%)';
    } else {
        container.style.backgroundColor = 'transparent';
    }

    const isDark = theme === 'dark';
    const edgeColor = '#a855f7'; // Purple edges matching the mockup

    // Pre-process elements to inject SVG backgrounds
    elements.forEach(el => {
        if (el.data && !el.data.source) {
            // It's a node
            // Assuming data contains: id, label (address), role, balance
            el.data.svgImage = generatePillNodeSVG(el.data.id, el.data.role, el.data.balance, isDark);
            el.data.cyLabel = ''; // Clear label since SVG handles it
        } else if (el.data && el.data.source) {
            // It's an edge
            const token = (el.data.asset || 'ETH').toUpperCase();
            const val = el.data.usd ? '$' + parseFloat(el.data.usd).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2}) : (el.data.value ? '$' + el.data.value : '');
            
            let addr = el.data.target;
            if(addr && addr.length > 10) {
                addr = addr.substring(0,6) + '...' + addr.substring(addr.length-4);
            }
            
            el.data.cyLabel = `${token}\nOUTFLOW\n↓ ${val}\n${addr}\n${token}`;
        }
    });

    const cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'width': '300px',
                    'height': '160px',
                    'shape': 'rectangle',
                    'background-image': 'data(svgImage)',
                    'background-fit': 'contain',
                    'background-opacity': 0, 
                    'border-width': 0,
                    'label': 'data(cyLabel)'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': edgeColor,
                    'target-arrow-color': edgeColor,
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(cyLabel)',
                    'font-size': '10px',
                    'font-weight': 'bold',
                    'color': '#475569',
                    'text-background-opacity': 1,
                    'text-background-color': '#ffffff',
                    'text-background-padding': '6px',
                    'text-background-shape': 'roundrectangle',
                    'text-border-width': 1,
                    'text-border-color': '#e2e8f0',
                    'text-wrap': 'wrap',
                    'text-halign': 'center',
                    'text-valign': 'center',
                    'edge-text-rotation': 'none',
                    'source-endpoint': 'outside-to-node',
                    'target-endpoint': 'outside-to-node',
                    'arrow-scale': 1.5,
                    'control-point-step-size': 100
                }
            }
        ],
        layout: {
            name: 'fcose',
            quality: 'proof',
            randomize: true,
            animate: true,
            animationDuration: 1000,
            fit: true,
            padding: 50,
            nodeDimensionsIncludeLabels: true,
            idealEdgeLength: edge => 300,
            nodeRepulsion: node => 450000
        }
    });

    return cy;
}

window.initNemesisGraph = initNemesisGraph;
window.generatePillNodeSVG = generatePillNodeSVG;
