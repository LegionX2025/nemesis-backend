// --- Header Scroll & Minimize Logic ---
const header = document.getElementById('global-header');
const toggleBtn = document.getElementById('header-toggle');
let isMinimized = false;

window.addEventListener('scroll', () => {
    if (isMinimized) return;
    if (window.scrollY > 50) {
        header.classList.add('shrunk');
    } else {
        header.classList.remove('shrunk');
    }
});

window.toggleHeader = () => {
    isMinimized = !isMinimized;
    if (isMinimized) {
        header.classList.add('minimized');
        toggleBtn.classList.add('visible');
    } else {
        header.classList.remove('minimized');
        toggleBtn.classList.remove('visible');
    }
};

// --- Three.js WebGL Cinematic Particle Network ---
const initWebGL = () => {
    const canvas = document.getElementById('nemesis-canvas');
    const container = document.getElementById('webgl-container');
    
    if (!canvas || !container) return; // safety check
    
    const scene = new THREE.Scene();
    
    // Camera
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 150;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Throttle for performance

    // Particles Geometry
    const particleCount = 400;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    for(let i=0; i<particleCount*3; i+=3) {
        positions[i] = (Math.random() - 0.5) * 400;     // x
        positions[i+1] = (Math.random() - 0.5) * 200;   // y
        positions[i+2] = (Math.random() - 0.5) * 200;   // z
        
        velocities.push({
            x: (Math.random() - 0.5) * 0.2,
            y: (Math.random() - 0.5) * 0.2,
            z: (Math.random() - 0.5) * 0.2
        });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    // Material
    const material = new THREE.PointsMaterial({
        color: 0x0ea5e9,
        size: 2,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Lines connecting particles
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x8b5cf6,
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending
    });
    
    // Generate empty buffer for lines (dynamic)
    const maxConnections = particleCount * 2;
    const linePositions = new Float32Array(maxConnections * 3 * 2);
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    // Mouse Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    container.addEventListener('mousemove', (e) => {
        const rect = container.getBoundingClientRect();
        mouseX = (e.clientX - rect.left) - (rect.width / 2);
        mouseY = (e.clientY - rect.top) - (rect.height / 2);
    });

    // Resize handler
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });

    // Animation Loop
    const clock = new THREE.Clock();
    
    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();

        // Smooth mouse tracking
        targetX = mouseX * 0.05;
        targetY = mouseY * 0.05;
        
        particles.rotation.y += 0.001;
        lines.rotation.y += 0.001;
        
        particles.rotation.x += (targetY * 0.01 - particles.rotation.x) * 0.05;
        particles.rotation.y += (targetX * 0.01 - particles.rotation.y) * 0.05;
        lines.rotation.x = particles.rotation.x;

        // Update particle positions
        const posAttribute = geometry.attributes.position;
        const posArray = posAttribute.array;
        
        let vertexIndex = 0;
        let numConnected = 0;

        for(let i=0; i<particleCount; i++) {
            const i3 = i * 3;
            
            // Move
            posArray[i3] += velocities[i].x;
            posArray[i3+1] += velocities[i].y;
            posArray[i3+2] += velocities[i].z;

            // Bounce off bounds
            if(Math.abs(posArray[i3]) > 200) velocities[i].x *= -1;
            if(Math.abs(posArray[i3+1]) > 100) velocities[i].y *= -1;
            if(Math.abs(posArray[i3+2]) > 100) velocities[i].z *= -1;

            // Check connections
            for(let j=i+1; j<particleCount; j++) {
                const j3 = j * 3;
                const dx = posArray[i3] - posArray[j3];
                const dy = posArray[i3+1] - posArray[j3+1];
                const dz = posArray[i3+2] - posArray[j3+2];
                const distSq = dx*dx + dy*dy + dz*dz;

                if(distSq < 1500 && numConnected < maxConnections) {
                    linePositions[vertexIndex++] = posArray[i3];
                    linePositions[vertexIndex++] = posArray[i3+1];
                    linePositions[vertexIndex++] = posArray[i3+2];
                    
                    linePositions[vertexIndex++] = posArray[j3];
                    linePositions[vertexIndex++] = posArray[j3+1];
                    linePositions[vertexIndex++] = posArray[j3+2];
                    numConnected++;
                }
            }
        }
        
        posAttribute.needsUpdate = true;
        lineGeometry.attributes.position.needsUpdate = true;
        lineGeometry.setDrawRange(0, numConnected * 2);

        renderer.render(scene, camera);
    }

    animate();
};

// Initialize WebGL once DOM is ready
document.addEventListener('DOMContentLoaded', initWebGL);
