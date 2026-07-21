document.addEventListener("DOMContentLoaded", () => {
    // Inject the container if it doesn't exist
    if (!document.getElementById("webgl-bg-container")) {
        const container = document.createElement("div");
        container.id = "webgl-bg-container";
        document.body.prepend(container);
    }
    
    initWebGLButterflies();
});

function initWebGLButterflies() {
    if (typeof THREE === 'undefined') {
        console.warn("Three.js not loaded. Butterflies disabled.");
        return;
    }

    const container = document.getElementById('webgl-bg-container');
    const scene = new THREE.Scene();
    
    // Transparent background
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    // Butterfly Class
    class Butterfly {
        constructor() {
            this.group = new THREE.Group();
            
            // Vibrant colors matching light modern themes (pinks, blues, purples, oranges)
            const colors = [0xff3366, 0x33ccff, 0x9933ff, 0xff9933, 0x00e676];
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            const material = new THREE.MeshPhongMaterial({ 
                color: color,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.85,
                shininess: 100
            });

            // Wings (Simple plane geometries)
            const geometry = new THREE.PlaneGeometry(1, 1.5);
            
            this.leftWing = new THREE.Mesh(geometry, material);
            this.leftWing.position.x = -0.5;
            // Shift pivot to the edge
            this.leftWing.geometry.translate(0.5, 0, 0);
            
            this.rightWing = new THREE.Mesh(geometry, material);
            this.rightWing.position.x = 0.5;
            this.rightWing.geometry.translate(-0.5, 0, 0);

            this.group.add(this.leftWing);
            this.group.add(this.rightWing);

            // Random initial position
            this.group.position.x = (Math.random() - 0.5) * 40;
            this.group.position.y = (Math.random() - 0.5) * 40;
            this.group.position.z = (Math.random() - 0.5) * 20 - 10;
            
            // Movement parameters
            this.speed = Math.random() * 0.05 + 0.02;
            this.angle = Math.random() * Math.PI * 2;
            this.flapSpeed = Math.random() * 0.2 + 0.3;
            
            scene.add(this.group);
        }

        update(time) {
            // Flap wings using sine wave
            const flap = Math.sin(time * this.flapSpeed * 10) * 0.8;
            this.leftWing.rotation.y = flap;
            this.rightWing.rotation.y = -flap;

            // Move around (gentle floating)
            this.group.position.x += Math.cos(this.angle) * this.speed;
            this.group.position.y += Math.sin(this.angle) * this.speed + Math.sin(time * 2) * 0.02;
            
            // Gently rotate towards movement direction
            this.group.rotation.z = this.angle - Math.PI/2;
            this.group.rotation.x = 0.2; // slight tilt forward

            // Slowly change angle
            this.angle += (Math.random() - 0.5) * 0.05;

            // Wrap around screen
            if (this.group.position.x > 25) this.group.position.x = -25;
            if (this.group.position.x < -25) this.group.position.x = 25;
            if (this.group.position.y > 25) this.group.position.y = -25;
            if (this.group.position.y < -25) this.group.position.y = 25;
        }
    }

    const butterflies = [];
    for(let i=0; i<15; i++) {
        butterflies.push(new Butterfly());
    }

    camera.position.z = 15;

    // Animation loop
    const clock = new THREE.Clock();
    function animate() {
        requestAnimationFrame(animate);
        const time = clock.getElapsedTime();
        
        butterflies.forEach(b => b.update(time));
        
        renderer.render(scene, camera);
    }
    
    animate();

    // Handle Resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}
