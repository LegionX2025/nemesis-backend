function switchView(viewId) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeNav = document.querySelector(`a[onclick="switchView('${viewId}')"]`);
    if(activeNav) activeNav.classList.add('active');

    document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
    document.getElementById('main-content').scrollTop = 0;
}

// --- Simulated LEA Localization ---
function localizeLEA() {
    const zip = document.getElementById('zip-code-input').value;
    const container = document.getElementById('lea-contacts');
    if(!zip || zip.length < 5) return alert("Please enter a valid US Zip Code.");
    
    // In a real app, this would query a backend API mapping ZIP codes to FBI Field Offices and local PDs.
    container.innerHTML = `
        <p class="font-bold text-blue-800 mb-4 uppercase tracking-widest text-xs border-b border-blue-200 pb-2">Law Enforcement Contacts for Region: ${zip}</p>
        <ul class="list-disc pl-5 space-y-3 text-slate-700">
            <li><strong>Local Police Department:</strong> Financial Crimes / Cyber Unit</li>
            <li><strong>State Authorities:</strong> State Attorney General's Cyber Fraud Unit</li>
            <li><strong>Federal (FBI):</strong> Nearest Field Office Cyber Task Force</li>
            <li><strong>Federal (Secret Service):</strong> Electronic Crimes Task Force (ECTF)</li>
            <li><strong>Mandatory Reporting Portal:</strong> <a href="https://www.ic3.gov/" target="_blank" class="text-blue-600 font-bold underline">IC3.gov</a></li>
        </ul>
        <div class="mt-4 p-3 bg-blue-100 border border-blue-200 rounded text-xs text-blue-800 font-bold">
            <i class="ph-fill ph-info"></i> Instruction: Provide this generated Forensic Trace Report as an official exhibit when filing your IC3 complaint.
        </div>
    `;
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
