document.addEventListener('DOMContentLoaded', () => {
    tsParticles.load("tsparticles", {
        background: {
            color: {
                value: "transparent",
            },
        },
        fpsLimit: 60,
        interactivity: {
            events: {
                onClick: {
                    enable: true,
                    mode: "push",
                },
                onHover: {
                    enable: true,
                    mode: "grab", 
                },
                resize: true,
            },
            modes: {
                push: {
                    quantity: 4,
                },
                grab: {
                    distance: 140,
                    links: {
                        opacity: 0.5,
                        color: "#00ffcc"
                    }
                }
            },
        },
        particles: {
            color: {
                value: ["#00ffcc", "#3b82f6", "#a855f7"],
            },
            links: {
                color: "#334155", 
                distance: 150,
                enable: true,
                opacity: 0.4,
                width: 1,
                triangles: {
                    enable: false
                }
            },
            collisions: {
                enable: false,
            },
            move: {
                direction: "none",
                enable: true,
                outModes: {
                    default: "bounce",
                },
                random: false,
                speed: 0.8,
                straight: false,
            },
            number: {
                density: {
                    enable: true,
                    area: 800,
                },
                value: 80,
            },
            opacity: {
                value: 0.6,
            },
            shape: {
                type: "circle",
            },
            size: {
                value: { min: 1, max: 3 },
            },
        },
        detectRetina: true,
    });
});
