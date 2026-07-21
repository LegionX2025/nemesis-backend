class QuantumNetworkBackground {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.resize();
        
        window.addEventListener('resize', () => this.resize());
        this.initParticles();
        this.animate();
        
        this.mouseX = 0;
        this.mouseY = 0;
        window.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });
    }

    resize() {
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.canvas.width = this.width;
        this.canvas.height = this.height;
    }

    initParticles() {
        this.particles = [];
        const numParticles = Math.floor((this.width * this.height) / 15000);
        for (let i = 0; i < numParticles; i++) {
            this.particles.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 1,
                color: this.getRandomColor()
            });
        }
    }

    getRandomColor() {
        const colors = [
            'rgba(37, 99, 235, 0.4)',  // Blue
            'rgba(16, 185, 129, 0.4)', // Emerald
            'rgba(139, 92, 246, 0.4)', // Violet
            'rgba(14, 165, 233, 0.4)'  // Sky
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    animate() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        // Draw elegant gradient background
        const gradient = this.ctx.createLinearGradient(0, 0, this.width, this.height);
        gradient.addColorStop(0, '#f8fafc');
        gradient.addColorStop(0.5, '#f1f5f9');
        gradient.addColorStop(1, '#e2e8f0');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.width, this.height);

        for (let i = 0; i < this.particles.length; i++) {
            let p = this.particles[i];
            
            p.x += p.vx;
            p.y += p.vy;
            
            if (p.x < 0 || p.x > this.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.height) p.vy *= -1;
            
            // Interaction with mouse
            let dx = this.mouseX - p.x;
            let dy = this.mouseY - p.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 150) {
                p.x -= dx * 0.01;
                p.y -= dy * 0.01;
            }

            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = p.color;
            this.ctx.fill();
            
            // Draw connections
            for (let j = i + 1; j < this.particles.length; j++) {
                let p2 = this.particles[j];
                let dx2 = p.x - p2.x;
                let dy2 = p.y - p2.y;
                let dist2 = Math.sqrt(dx2*dx2 + dy2*dy2);
                
                if (dist2 < 120) {
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(148, 163, 184, ${0.15 * (1 - dist2/120)})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.moveTo(p.x, p.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

// Auto-init if canvas exists
document.addEventListener('DOMContentLoaded', () => {
    new QuantumNetworkBackground('quantum-bg');
    
    // Add glowing border effects to inputs
    document.querySelectorAll('.input-container').forEach(container => {
        const input = container.querySelector('input');
        if(input) {
            input.addEventListener('focus', () => container.classList.add('glow-active'));
            input.addEventListener('blur', () => container.classList.remove('glow-active'));
        }
    });

    // Add widget controls
    document.querySelectorAll('.widget-control-min').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const widgetContent = e.target.closest('.widget-container').querySelector('.widget-content');
            if(widgetContent) {
                widgetContent.classList.toggle('hidden');
            }
        });
    });
    
    document.querySelectorAll('.widget-control-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const widget = e.target.closest('.widget-container');
            if(widget) {
                widget.style.display = 'none';
            }
        });
    });
});
