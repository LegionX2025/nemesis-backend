// theme.js - Global Web3GL Light Theme configuration

document.addEventListener("DOMContentLoaded", () => {
    // 1. Inject background container if it doesn't exist
    let bgDiv = document.getElementById("vanta-bg");
    if (!bgDiv) {
        bgDiv = document.createElement("div");
        bgDiv.id = "vanta-bg";
        // Fixed positioned background behind everything
        bgDiv.style.position = "fixed";
        bgDiv.style.inset = "0";
        bgDiv.style.zIndex = "-1";
        bgDiv.style.pointerEvents = "none";
        document.body.appendChild(bgDiv);
    }
    
    // Apply Light Theme base styles to body
    document.body.style.backgroundColor = "#f8fafc"; // Light slate background
    document.body.style.color = "#1e293b"; // Dark text
    
    // 2. Load Three.js and Vanta.js dynamically if not present
    function loadScript(src, callback) {
        if (document.querySelector(`script[src="${src}"]`)) {
            if (callback) callback();
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.onload = callback;
        document.head.appendChild(script);
    }

    loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js", () => {
        loadScript("https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.net.min.js", () => {
            if (window.VANTA && window.VANTA.NET) {
                // Initialize Light Theme Web3GL Particles
                window.vantaEffect = VANTA.NET({
                    el: "#vanta-bg",
                    mouseControls: true,
                    touchControls: true,
                    gyroControls: false,
                    minHeight: 200.00,
                    minWidth: 200.00,
                    scale: 1.00,
                    scaleMobile: 1.00,
                    color: 0x3b82f6, // Bright blue nodes (Web3 feel)
                    backgroundColor: 0xf8fafc, // Light background
                    points: 14.00,
                    maxDistance: 20.00,
                    spacing: 16.00,
                    showDots: true
                });
            }
        });
    });
});
