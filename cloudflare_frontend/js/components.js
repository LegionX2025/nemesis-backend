// components.js - Global Components for NEMESIS Light Theme Architecture

const GlobalComponents = {
    init: function() {
        this.injectHeader();
        this.injectFooter();
        this.initWebGLBackground();
        this.initWidgetControls();
    },

    injectHeader: function() {
        const headerHTML = `
        <header class="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-6 z-50 sticky top-0 shadow-sm transition-all duration-300">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-lion text-3xl text-blue-600 drop-shadow-sm"></i>
                <div class="flex flex-col group cursor-pointer" onclick="window.location.href='/'">
                    <span class="font-black text-2xl tracking-tight leading-none text-slate-800 uppercase bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-600 group-hover:from-indigo-600 group-hover:to-blue-700 transition-all duration-500">NEMESIS</span>
                    <span class="text-[9px] text-slate-500 font-bold tracking-widest uppercase mt-0.5 group-hover:text-blue-500 transition-colors">By Lionsgate Intelligence Network</span>
                </div>
            </div>

            <nav class="hidden lg:flex items-center gap-6">
                <a href="/" class="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-blue-600 hover:after:w-full after:transition-all">Home</a>
                <a href="/tracer.html" class="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-blue-600 hover:after:w-full after:transition-all">NEMESIS TRACER</a>
                <a href="/nemesis_id.html" class="text-sm font-bold text-slate-600 hover:text-blue-600 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-blue-600 hover:after:w-full after:transition-all">NEMESIS ID</a>
                <a href="/omega.html" class="text-sm font-bold text-slate-600 hover:text-indigo-600 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-indigo-600 hover:after:w-full after:transition-all"><i class="fa-solid fa-microchip"></i> OMEGA</a>
                <a href="/admin.html" class="text-sm font-bold text-slate-600 hover:text-red-600 transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 after:bg-red-600 hover:after:w-full after:transition-all"><i class="fa-solid fa-shield-halved"></i> ADMIN</a>
            </nav>

            <div class="flex items-center gap-5 text-slate-500 justify-end">
                <button class="hover:text-blue-600 transition-transform hover:scale-110"><i class="fa-regular fa-sun text-lg"></i></button>
                <button class="hover:text-blue-600 transition-transform hover:scale-110"><i class="fa-regular fa-bell text-lg"></i></button>
                <div class="h-6 w-px bg-slate-300 mx-1"></div>
                <div class="flex items-center gap-2 cursor-pointer hover:bg-slate-50 p-1.5 rounded-lg transition">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-md">AN</div>
                    <div class="hidden md:block text-left leading-tight">
                        <div class="text-xs font-bold text-slate-800">Analyst</div>
                        <div class="text-[9px] text-slate-500 font-semibold">Lionsgate Network</div>
                    </div>
                </div>
            </div>
        </header>
        `;
        document.body.insertAdjacentHTML('afterbegin', headerHTML);
    },

    injectFooter: function() {
        const footerHTML = `
        <footer class="h-12 bg-white/80 backdrop-blur-md border-t border-slate-200 flex items-center justify-between px-6 z-40 fixed bottom-0 w-full text-[10px] text-slate-500 font-semibold shadow-[0_-2px_10px_rgba(0,0,0,0.02)]">
            <div class="flex gap-4">
                <a href="#" class="hover:text-blue-600 transition">API Documentation</a>
                <a href="#" class="hover:text-blue-600 transition">Terms of Service</a>
                <a href="#" class="hover:text-blue-600 transition">Privacy Policy</a>
            </div>
            <div class="tracking-widest uppercase">
                &copy; 2026 LIONSGATE NEMESIS. ALL RIGHTS RESERVED.
            </div>
        </footer>
        `;
        document.body.insertAdjacentHTML('beforeend', footerHTML);
        document.body.style.paddingBottom = "3rem";
    },

    initWebGLBackground: function() {
        if(!document.getElementById('vanta-bg')) {
            const bg = document.createElement('div');
            bg.id = 'vanta-bg';
            bg.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-1; pointer-events:none; opacity: 0.6;';
            document.body.appendChild(bg);
        }

        const loadScript = (src) => {
            return new Promise((resolve) => {
                if(document.querySelector(`script[src="${src}"]`)) return resolve();
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                document.head.appendChild(script);
            });
        };

        loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js').then(() => {
            loadScript('https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.net.min.js').then(() => {
                if(window.VANTA) {
                    window.VANTA.NET({
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
                        maxDistance: 22.00,
                        spacing: 18.00,
                        showDots: true
                    });
                }
            });
        });
    },

    initWidgetControls: function() {
        setTimeout(() => {
            document.querySelectorAll('.widget-panel').forEach(panel => {
                const header = panel.querySelector('.widget-header');
                if(!header) return;

                const controls = document.createElement('div');
                controls.className = 'flex gap-2 text-slate-400 ml-auto';
                controls.innerHTML = `
                    <i class="fa-solid fa-minus cursor-pointer hover:text-blue-500 transition btn-minimize" title="Minimize"></i>
                    <i class="fa-solid fa-expand cursor-pointer hover:text-emerald-500 transition btn-expand" title="Maximize"></i>
                    <i class="fa-solid fa-xmark cursor-pointer hover:text-red-500 transition btn-close" title="Close"></i>
                `;
                header.appendChild(controls);

                const content = panel.querySelector('.widget-content');
                controls.querySelector('.btn-minimize').addEventListener('click', (e) => {
                    e.stopPropagation();
                    if(content) content.classList.toggle('hidden');
                    panel.classList.toggle('h-auto');
                });

                controls.querySelector('.btn-expand').addEventListener('click', (e) => {
                    e.stopPropagation();
                    panel.classList.toggle('fixed');
                    panel.classList.toggle('inset-4');
                    panel.classList.toggle('z-[100]');
                    panel.classList.toggle('shadow-2xl');
                    if(panel.classList.contains('fixed')) {
                        panel.style.width = 'calc(100vw - 2rem)';
                        panel.style.height = 'calc(100vh - 5rem)';
                        if(content) content.style.height = 'calc(100% - 3rem)';
                    } else {
                        panel.style.width = '';
                        panel.style.height = '';
                        if(content) content.style.height = '';
                    }
                });

                controls.querySelector('.btn-close').addEventListener('click', (e) => {
                    e.stopPropagation();
                    panel.style.display = 'none';
                });
            });
        }, 1000);
    }
};

window.addEventListener('DOMContentLoaded', () => {
    GlobalComponents.init();
});
