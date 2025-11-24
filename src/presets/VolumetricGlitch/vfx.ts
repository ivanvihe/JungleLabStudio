import * as THREE from 'three';

let scene: THREE.Scene;

// --- Arcs System ---
let arcSystem: THREE.Points;
let arcParticles: any[] = [];
const ARC_COUNT = 100;

// --- Trails System ---
let trailSystem: THREE.Line;
let trailParticles: any[] = [];
const TRAIL_COUNT = 50;

// --- Fluid System ---
let fluidSystem: THREE.Points;
let fluidParticles: any[] = [];
const FLUID_COUNT = 500;

export const createVFX = (s: THREE.Scene) => {
    scene = s;

    // Arcs
    const arcGeometry = new THREE.BufferGeometry();
    arcGeometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(ARC_COUNT * 3), 3));
    const arcMaterial = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.1, transparent: true, blending: THREE.AdditiveBlending });
    arcSystem = new THREE.Points(arcGeometry, arcMaterial);
    scene.add(arcSystem);
    for (let i = 0; i < ARC_COUNT; i++) {
        arcParticles.push({
            angle: Math.random() * Math.PI * 2,
            radius: 2 + Math.random() * 3,
            speed: 0.1 + Math.random() * 0.2,
            life: 0
        });
    }

    // Trails
    const trailGeometry = new THREE.BufferGeometry();
    trailGeometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(TRAIL_COUNT * 3), 3));
    const trailMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 });
    trailSystem = new THREE.Line(trailGeometry, trailMaterial);
    scene.add(trailSystem);
    for (let i = 0; i < TRAIL_COUNT; i++) {
        trailParticles.push({
            position: new THREE.Vector3((Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10),
            velocity: new THREE.Vector3((Math.random() - 0.5) * 0.1, (Math.random() - 0.5) * 0.1, 0),
            life: 0
        });
    }

    // Fluid
    const fluidGeometry = new THREE.BufferGeometry();
    fluidGeometry.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(FLUID_COUNT * 3), 3));
    const fluidMaterial = new THREE.PointsMaterial({ color: 0xff00ff, size: 0.2, transparent: true, blending: THREE.AdditiveBlending, opacity: 0.3 });
    fluidSystem = new THREE.Points(fluidGeometry, fluidMaterial);
    scene.add(fluidSystem);
    for (let i = 0; i < FLUID_COUNT; i++) {
        fluidParticles.push({
            position: new THREE.Vector3(),
            velocity: new THREE.Vector3(),
            life: 0
        });
    }
};

export const updateVFX = (deltaTime: number, audioData: any) => {
    // Arcs
    const arcPositions = arcSystem.geometry.attributes.position as THREE.BufferAttribute;
    arcParticles.forEach((p, i) => {
        p.angle += p.speed * deltaTime;
        const x = Math.cos(p.angle) * p.radius;
        const y = Math.sin(p.angle) * p.radius;
        arcPositions.setXYZ(i, x, y, 0);
    });
    arcSystem.geometry.attributes.position.needsUpdate = true;

    // Trails
    const trailPositions = trailSystem.geometry.attributes.position as THREE.BufferAttribute;
    trailParticles.forEach((p, i) => {
        p.position.add(p.velocity);
        trailPositions.setXYZ(i, p.position.x, p.position.y, p.position.z);
        if (p.position.x > 5 || p.position.x < -5) p.velocity.x *= -1;
        if (p.position.y > 5 || p.position.y < -5) p.velocity.y *= -1;
    });
    trailSystem.geometry.attributes.position.needsUpdate = true;

    // Fluid
    const fluidPositions = fluidSystem.geometry.attributes.position as THREE.BufferAttribute;
    fluidParticles.forEach((p, i) => {
        p.velocity.x += (Math.random() - 0.5) * 0.1 * audioData.mid;
        p.velocity.y += (Math.random() - 0.5) * 0.1 * audioData.mid;
        p.position.add(p.velocity.multiplyScalar(deltaTime));
        fluidPositions.setXYZ(i, p.position.x, p.position.y, p.position.z);
        if (p.position.length() > 5) p.position.set(0,0,0);
    });
    fluidSystem.geometry.attributes.position.needsUpdate = true;
};