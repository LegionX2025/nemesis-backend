const originalWarn = console.warn;
console.warn = function(...args) {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('cdn.tailwindcss.com should not be used in production')) return;
    originalWarn.apply(console, args);
};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Vanta NET Background (Light Theme)
    if (window.VANTA) {
        VANTA.NET({
            el: "#vanta-bg",
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.00,
            minWidth: 200.00,
            scale: 1.00,
            scaleMobile: 1.00,
            color: 0x3b82f6,
            backgroundColor: 0xf8fafc,
            points: 15.00,
            maxDistance: 25.00,
            spacing: 18.00,
            showDots: true
        });
    }
});
