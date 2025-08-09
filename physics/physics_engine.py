import pybullet as p
import pybullet_data
import numpy as np

class PhysicsEngine:
    def __init__(self):
        self.client_id = p.connect(p.DIRECT) # p.GUI for visual debugging, p.DIRECT for no GUI
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.setTimeStep(1./240.) # Slow down simulation for debugging
        self.particles = []
        self.plane_id = None

        # Create a ground plane
        self.plane_id = p.createCollisionShape(p.GEOM_PLANE)
        p.createMultiBody(0, self.plane_id, basePosition=[0,0,-5]) # Move ground plane down

        # Add a static box for debugging visibility
        box_half_extents = [1, 1, 1]
        box_visual_shape_id = p.createVisualShape(p.GEOM_BOX, halfExtents=box_half_extents, rgbaColor=[1, 0, 0, 1])
        box_collision_shape_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=box_half_extents)
        p.createMultiBody(0, box_collision_shape_id, box_visual_shape_id, [0, 0, 0]) # Box at origin

    def create_fluid_particles(self, num_particles):
        # Create small spheres as particles
        radius = 0.05
        mass = 0.1
        visual_shape_id = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=[0.2, 0.2, 0.8, 0.8])
        collision_shape_id = p.createCollisionShape(p.GEOM_SPHERE, radius=radius)

        for i in range(num_particles):
            # Random initial positions above the plane
            x = np.random.uniform(-1, 1)
            y = np.random.uniform(-1, 1)
            z = np.random.uniform(5, 10) # Start much higher up
            position = [x, y, z]
            orientation = p.getQuaternionFromEuler([0, 0, 0])
            
            body_id = p.createMultiBody(mass, collision_shape_id, visual_shape_id, position, orientation)
            self.particles.append(body_id)
        print(f"Created {len(self.particles)} PyBullet particles.")
        return self.get_particle_positions()

    def get_particle_positions(self):
        positions = []
        for particle_id in self.particles:
            pos, _ = p.getBasePositionAndOrientation(particle_id)
            positions.append(list(pos))
        return np.array(positions, dtype=np.float32)

    def step_simulation(self):
        p.stepSimulation()

    def disconnect(self):
        p.disconnect()