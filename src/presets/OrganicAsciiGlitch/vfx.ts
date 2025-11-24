import * as THREE from 'three';

let particleSystem: THREE.Points;
let particles: {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  life: number;
  maxLife: number;
}[];

const PARTICLE_COUNT = 5000;

export const createParticleSystem = (scene: THREE.Scene) => {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const colors = new Float32Array(PARTICLE_COUNT * 3);

  particles = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    positions[i * 3] = 0;
    positions[i * 3 + 1] = 0;
    positions[i * 3 + 2] = 0;
    colors[i * 3] = 1;
    colors[i * 3 + 1] = 1;
    colors[i * 3 + 2] = 1;
    
    particles.push({
        position: new THREE.Vector3(0,0,0),
        velocity: new THREE.Vector3(0,0,0),
        life: 0,
        maxLife: 0
    });
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.1,
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false,
  });

  particleSystem = new THREE.Points(geometry, material);
  scene.add(particleSystem);
};

export const updateParticles = (deltaTime: number, audioData: any, config: any) => {
  const positions = particleSystem.geometry.attributes.position.array as Float32Array;
  const colors = particleSystem.geometry.attributes.color.array as Float32Array;

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const p = particles[i];
    if (p.life > 0) {
      p.life -= deltaTime;

      p.velocity.y -= 0.1 * deltaTime; // gravity
      p.position.add(p.velocity.clone().multiplyScalar(deltaTime));

      positions[i * 3] = p.position.x;
      positions[i * 3 + 1] = p.position.y;
      positions[i * 3 + 2] = p.position.z;

      const lifeRatio = p.life / p.maxLife;
      colors[i * 3] = lifeRatio;
      colors[i * 3 + 1] = lifeRatio;
      colors[i * 3 + 2] = 1;
    } else {
        positions[i*3+1] = -1000; // hide particle
    }
  }

  particleSystem.geometry.attributes.position.needsUpdate = true;
  particleSystem.geometry.attributes.color.needsUpdate = true;
};

export const triggerParticleBurst = (count: number, intensity: number, color: string) => {
    let activatedCount = 0;
    for (let i = 0; i < PARTICLE_COUNT && activatedCount < count; i++) {
        const p = particles[i];
        if (p.life <= 0) {
            p.position.set(0,0,0);
            const spread = 5 * intensity;
            p.velocity.set(
                (Math.random() - 0.5) * spread,
                (Math.random() - 0.5) * spread,
                (Math.random() - 0.5) * spread
            );
            p.maxLife = p.life = Math.random() * 2 + 1;
            activatedCount++;
        }
    }
}

export const applyVFX = (canvas: HTMLCanvasElement, audioData: any) => {
  // Not used in this preset
};