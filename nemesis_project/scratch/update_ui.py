import re

def update_html():
    path = "C:/Users/LEGIONX/Downloads/cases/nemesis_project/templates/nemesis_tracer.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
        
    # 1. Add id="dashboard-sidebar" to Col 1
    if 'id="dashboard-sidebar"' not in html:
        html = html.replace(
            '<div class="w-64 border-r border-slate-100 p-4 flex flex-col gap-4 overflow-y-auto shrink-0 hidden md:flex">',
            '<div class="w-64 border-r border-slate-100 p-4 flex flex-col gap-4 overflow-y-auto shrink-0 hidden md:flex transition-all duration-300" id="dashboard-sidebar">'
        )
        
    # 2. Add the toggle button in the floating Top Toolbar of the graph
    target_btn_html = '''                                    <!-- Left: Layouts & Filters -->
                                    <div class="flex gap-2 pointer-events-auto">
                                        <button onclick="toggleSidebar()" id="sidebar-toggle" class="bg-white/90 backdrop-blur-md border border-slate-200/60 p-1.5 rounded-lg shadow-lg flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-slate-100 transition-colors w-8 tooltip" data-tip="Toggle Dashboard">
                                            <i class="fa-solid fa-bars-staggered"></i>
                                        </button>'''
    if 'id="sidebar-toggle"' not in html:
        html = html.replace(
            '''                                    <!-- Left: Layouts & Filters -->
                                    <div class="flex gap-2 pointer-events-auto">''',
            target_btn_html
        )
        
    # 3. Add JS functions for togglePanel, maximizePanel, toggleSidebar
    js_funcs = """
            function toggleSidebar() {
                const sidebar = document.getElementById('dashboard-sidebar');
                const toggleBtn = document.getElementById('sidebar-toggle').querySelector('i');
                if (!sidebar) return;
                
                if (sidebar.style.width === '0px' || sidebar.classList.contains('hidden-sidebar')) {
                    sidebar.classList.remove('hidden-sidebar');
                    sidebar.style.width = '16rem';
                    sidebar.style.opacity = '1';
                    sidebar.style.padding = '1rem';
                    toggleBtn.classList.replace('fa-indent', 'fa-bars-staggered');
                } else {
                    sidebar.classList.add('hidden-sidebar');
                    sidebar.style.width = '0px';
                    sidebar.style.opacity = '0';
                    sidebar.style.padding = '0';
                    sidebar.style.overflow = 'hidden';
                    toggleBtn.classList.replace('fa-bars-staggered', 'fa-indent');
                }
            }
            
            function togglePanel(panelId) {
                const panel = document.getElementById(panelId);
                if (!panel) return;
                let body = panel.querySelector('[id$="-body"]');
                if (!body && panelId === 'panel-scenario') body = document.getElementById('panel-scenario-body');
                if (!body && panelId === 'panel-main') body = document.getElementById('panel-main-body');
                
                if (!body) return;
                if (body.style.display === 'none' || body.classList.contains('hidden')) {
                    body.style.display = 'flex';
                    body.classList.remove('hidden');
                    panel.style.flexGrow = '1';
                } else {
                    body.style.display = 'none';
                    body.classList.add('hidden');
                    panel.style.flexGrow = '0';
                }
            }
            
            function maximizePanel(panelId) {
                const panel = document.getElementById(panelId);
                if (!panel) return;
                
                if (panel.classList.contains('fixed')) {
                    panel.classList.remove('fixed', 'inset-4', 'z-[200]', 'shadow-2xl');
                    document.body.style.overflow = '';
                } else {
                    panel.classList.add('fixed', 'inset-4', 'z-[200]', 'shadow-2xl');
                    document.body.style.overflow = 'hidden';
                }
            }
"""
    if "function toggleSidebar()" not in html:
        html = html.replace('function toggleTraceControls() {', js_funcs + '\n            function toggleTraceControls() {')
        
    # 4. Auto hide the panel-scenario and sidebar in INIT WS
    init_hook = """
                    // Auto Hide Panels to maximize graph space
                    toggleSidebar(); // hide left dashboard
                    let scenarioPanelBody = document.getElementById('panel-scenario-body');
                    if (scenarioPanelBody && scenarioPanelBody.style.display !== 'none') {
                        togglePanel('panel-scenario');
                    }
"""
    if "// Auto Hide Panels to maximize graph space" not in html:
        html = html.replace(
            'document.getElementById("ajax-loader-text").innerText = "Initializing trace nodes...";\n                    }',
            'document.getElementById("ajax-loader-text").innerText = "Initializing trace nodes...";\n                    }\n' + init_hook
        )
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print("UI update successful.")

if __name__ == "__main__":
    update_html()
