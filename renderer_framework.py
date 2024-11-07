import pygame
import math
import numpy as np
import json

"""
Units: mm
"""

# Settings
POINTS_FILE = 'points.json'
GRID_FILE = 'grid.json'
WIDTH, HEIGHT = 950, 800
background_color = (20, 20, 20)
MAX_FPS = 60 #0-60

# Initialize Pygame
pygame.init()

# Screen settings
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fusor Grid")

# default colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)

# font init
font = pygame.font.Font(None, 20)

# Points class
class Point:
    def __init__(self, x, y, z, color=WHITE):
        self.x = x
        self.y = y
        self.z = z
        self.color = color
    def project_to_2d(self, camera):
        return camera.project_point((self.x, self.y, self.z))
    @classmethod
    def from_dict(cls, data):
        return cls(data['x'], data['y'], data['z'], tuple(data['color']))

# load points from json
def load_points(filename=POINTS_FILE):
    with open(filename, 'r') as file:
        points_data = json.load(file)
    return [Point.from_dict(data) for data in points_data]

try:
    points = load_points(POINTS_FILE)
except FileNotFoundError:
    print("points Json missing")
    points = []

# Ring Class 
class Ring:
    def __init__(self, radius, center_x, center_y, center_z, segments=50):
        self.radius = radius
        self.center_x = center_x
        self.center_y = center_y
        self.center_z = center_z
        self.num_segments = segments
    
    def generate_points(self):
        points = []
        
        # Step 1: Calculate the normal vector (from ring center to origin)
        normal_x = -self.center_x
        normal_y = -self.center_y
        normal_z = -self.center_z
        
        # Normalize the normal vector to get a unit vector
        norm = math.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        normal_x /= norm
        normal_y /= norm
        normal_z /= norm
        
        # Step 2: Calculate the axis of rotation and the angle required
        # The ring is initially in the x-y plane (normal = (0, 0, 1))
        initial_normal = np.array([0, 0, 1])
        ring_normal = np.array([normal_x, normal_y, normal_z])
        
        # Compute the axis of rotation (cross product of initial_normal and ring_normal)
        axis_of_rotation = np.cross(initial_normal, ring_normal)
        axis_of_rotation_norm = np.linalg.norm(axis_of_rotation)
        
        if axis_of_rotation_norm > 1e-6:  # Avoid division by zero
            axis_of_rotation /= axis_of_rotation_norm
        else:
            axis_of_rotation = np.array([1, 0, 0])  # Arbitrary if no rotation is needed
        
        # Compute the angle between the two vectors (dot product)
        dot_product = np.dot(initial_normal, ring_normal)
        angle = math.acos(dot_product)
        
        # Step 3: Generate the points in the ring (in the x-y plane initially)
        for i in range(self.num_segments):
            theta = 2 * math.pi * i / self.num_segments
            x = self.radius * math.cos(theta)
            y = self.radius * math.sin(theta)
            z = 0  # Initially the ring lies in the x-y plane
            
            # Step 4: Rotate the points around the axis_of_rotation by the angle
            rotation_matrix = self.rotation_matrix(axis_of_rotation, angle)
            point = np.array([x, y, z])
            rotated_point = np.dot(rotation_matrix, point)
            
            # Step 5: Translate the rotated points to the ring's center
            points.append((rotated_point[0] + self.center_x, rotated_point[1] + self.center_y, rotated_point[2] + self.center_z))
        
        return points
    
    def rotation_matrix(self, axis, theta):
        """Generates a rotation matrix for rotating points around a given axis by angle theta"""
        axis = axis / np.linalg.norm(axis)  # Normalize the axis
        
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        ux, uy, uz = axis
        
        # 3x3 rotation matrix (Rodrigues' rotation formula)
        rotation_matrix = np.array([
            [cos_theta + ux**2 * (1 - cos_theta), ux * uy * (1 - cos_theta) - uz * sin_theta, ux * uz * (1 - cos_theta) + uy * sin_theta],
            [uy * ux * (1 - cos_theta) + uz * sin_theta, cos_theta + uy**2 * (1 - cos_theta), uy * uz * (1 - cos_theta) - ux * sin_theta],
            [uz * ux * (1 - cos_theta) - uy * sin_theta, uz * uy * (1 - cos_theta) + ux * sin_theta, cos_theta + uz**2 * (1 - cos_theta)]
        ])
        
        return rotation_matrix

    @classmethod
    def from_dict(cls, data):
        return cls(data['radius'], data['center_x'], data['center_y'], data['center_z'], data['segments'])
    
    def generate_edges(self):
        points = self.generate_points()
        edges = []
        
        # Connect consecutive points with edges (segments)
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]  # Wrap around to the first point
            
            edges.append((start_point, end_point))
        
        return edges



def load_rings(filename=GRID_FILE):
    with open(filename, 'r') as file:
        ring_data = json.load(file)
    return [Ring.from_dict(data) for data in ring_data]

try:
    rings = load_rings(GRID_FILE)
except FileNotFoundError:
    print("ring Json missing")
    rings = []

# Camera Rotation Class
class Camera:
    def __init__(self, distance):
        self.distance = distance  # Distance from the origin
        self.angle_x = 0  # Rotation angle around x-axis
        self.angle_y = 0  # Rotation angle around y-axis

    def rotate(self, delta_x, delta_y):
        self.angle_x -= delta_y
        self.angle_y += delta_x

    def get_projection_matrix(self):
        # Rotation matrix around x-axis
        rotation_x = np.array([
            [1, 0, 0],
            [0, math.cos(self.angle_x), -math.sin(self.angle_x)],
            [0, math.sin(self.angle_x), math.cos(self.angle_x)]
        ])
        
        # Rotation matrix around y-axis
        rotation_y = np.array([
            [math.cos(self.angle_y), 0, math.sin(self.angle_y)],
            [0, 1, 0],
            [-math.sin(self.angle_y), 0, math.cos(self.angle_y)]
        ])
        
        # Combine rotations
        return rotation_y @ rotation_x

    def project_point(self, point):
        # Camera projection (perspective)
        projection_matrix = self.get_projection_matrix()
        rotated_point = projection_matrix @ np.array(point)
        
        # Perspective division (simple projection)
        factor = self.distance / (self.distance + rotated_point[2])
        x_proj = rotated_point[0] * factor
        y_proj = rotated_point[1] * factor
        
        return x_proj, y_proj

# Main Loop
def main():
    clock = pygame.time.Clock()
    camera = Camera(distance=1000)
    
    running = True
    while running:
        screen.fill(background_color)
        
        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                # Rotate the camera based on mouse movement
                camera.rotate(event.rel[0] * 0.005, event.rel[1] * 0.005)

        fps = clock.get_fps()

        # Draw all points
        for point in points:
            projected_x, projected_y = point.project_to_2d(camera)
            screen_x = int(projected_x + WIDTH // 2)
            screen_y = int(projected_y + HEIGHT // 2)
            pygame.draw.circle(screen, point.color, (screen_x, screen_y), 1)
        
        # Draw all rings
        for ring in rings:
            edges = ring.generate_edges()
            for start_point, end_point in edges:
                # Project the start and end points
                x1, y1 = camera.project_point(start_point)
                x2, y2 = camera.project_point(end_point)
                # Draw the line segment between the two projected points
                pygame.draw.line(screen, LIGHT_GRAY, (x1 + WIDTH / 2, y1 + HEIGHT / 2), (x2 + WIDTH / 2, y2 + HEIGHT / 2), 5)

        # Draw text
        text_surface = font.render(f"FPS: {int(fps)}", True, WHITE)
        text_rect = text_surface.get_rect(center=(50, 50))
        screen.blit(text_surface, text_rect)

        # Update display
        pygame.display.flip()
        clock.tick(MAX_FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
