import pygame
import math
import numpy as np
import json

# Settings
points_file = 'points.json'
grid_file = 'grid.json'

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fusor Grid")

# default colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

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
def load_points(filename=points_file):
    with open(filename, 'r') as file:
        points_data = json.load(file)
    return [Point.from_dict(data) for data in points_data]

try:
    points = load_points(points_file)
except FileNotFoundError:
    print("points Json missing")
    points = []

# Ring Class 
class Ring:
    def __init__(self, radius, major_axis_angle, distance_from_origin, segments=50):
        self.radius = radius
        self.major_axis_angle = major_axis_angle  # In degrees
        self.distance_from_origin = distance_from_origin
        self.num_segments = segments  # Number of segments around the ring
    
    def generate_points(self):
        points = []
        # Convert major axis angle to radians
        angle_rad = math.radians(self.major_axis_angle)
        
        for i in range(self.num_segments):
            theta = 2 * math.pi * i / self.num_segments
            x = self.radius * math.cos(theta)
            y = self.radius * math.sin(theta)
            z = 0  # Assume the ring lies on the x-y plane
            
            # Rotate the points around the y-axis by the major axis angle
            x_rot = x * math.cos(angle_rad) + z * math.sin(angle_rad)
            z_rot = -x * math.sin(angle_rad) + z * math.cos(angle_rad)
            
            # Translate along the z-axis by distance_from_origin
            points.append((x_rot, y, self.distance_from_origin + z_rot))
        
        return points
    @classmethod
    def from_dict(cls, data):
        return cls(data['radius'], data['major_axis_angle'], data['distance_from_origin'], data['segments'])
    
    def generate_edges(self):
        points = self.generate_points()
        edges = []
        
        # Connect consecutive points with edges (segments)
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]  # Wrap around to the first point
            
            edges.append((start_point, end_point))
        
        return edges

def load_rings(filename=grid_file):
    with open(filename, 'r') as file:
        ring_data = json.load(file)
    return [Ring.from_dict(data) for data in ring_data]

try:
    rings = load_rings(grid_file)
except FileNotFoundError:
    print("ring Json missing")
    rings = []

# Camera Rotation Class (Same as before)
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
    
    # Create camera and rings
    camera = Camera(distance=500)
    
    running = True
    while running:
        screen.fill(BLACK)
        
        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                # Rotate the camera based on mouse movement
                camera.rotate(event.rel[0] * 0.005, event.rel[1] * 0.005)
        
        # Draw all rings
        for ring in rings:
            edges = ring.generate_edges()
            for start_point, end_point in edges:
                # Project the start and end points
                x1, y1 = camera.project_point(start_point)
                x2, y2 = camera.project_point(end_point)
                
                # Draw the line segment between the two projected points
                pygame.draw.line(screen, WHITE, (x1 + WIDTH / 2, y1 + HEIGHT / 2), (x2 + WIDTH / 2, y2 + HEIGHT / 2), 1)
        
        # Draw all points
        for point in points:
            projected_x, projected_y = point.project_to_2d(camera)
            screen_x = int(projected_x + WIDTH // 2)
            screen_y = int(projected_y + HEIGHT // 2)
            pygame.draw.circle(screen, point.color, (screen_x, screen_y), 1)

        # Draw text
        text_surface = font.render('Test', True, WHITE)
        text_rect = text_surface.get_rect(center=(50, 50))
        screen.blit(text_surface, text_rect)

        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
