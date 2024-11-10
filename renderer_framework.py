import pygame
import math
import numpy as np
import json

# Settings
POINTS_FILE = 'points.json'
GRID_FILE = 'grid.json'
WIDTH, HEIGHT = 950, 800
background_color = (20, 20, 20)
MAX_FPS = 60 #0-60
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)

# Initialize Pygame
pygame.init()

# Screen settings
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fusor Grid")

# font init
font = pygame.font.Font(None, 20)

# Points class
class Point:
    def __init__(self, x, y, z, color=WHITE):
        self.x, self.y, self.z = x, y, z
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

class Ring:
    def __init__(self, radius, x_c, y_c, z_c, x_ang, y_ang, z_ang, segments=50):
        self.radius = radius
        self.x_c, self.y_c, self.z_c = x_c, y_c, z_c
        self.x_ang, self.y_ang, self.z_ang = x_ang, y_ang, z_ang
        self.segments = segments

    def generate_points(self):
        points = []
        rotation_matrix = self.rotation_matrix(self.x_ang, self.y_ang, self.z_ang)
        
        for i in range(self.segments):
            theta = 2 * math.pi * i / self.segments
            x = self.radius * math.cos(theta)
            y = self.radius * math.sin(theta)
            z = 0

            rotated_point = rotation_matrix @ np.array([x, y, z])
            points.append((rotated_point[0] + self.x_c, rotated_point[1] + self.y_c, rotated_point[2] + self.z_c))
        
        return points

    def rotation_matrix(self, x_ang, y_ang, z_ang):
        a = math.radians(x_ang)
        b = math.radians(y_ang)
        g = math.radians(z_ang)
        
        rot_x = np.array([
            [1, 0, 0],
            [0, math.cos(a), -math.sin(a)],
            [0, math.sin(a), math.cos(a)]
        ])
        
        rot_y = np.array([
            [math.cos(b), 0, math.sin(b)],
            [0, 1, 0],
            [-math.sin(b), 0, math.cos(b)]
        ])
        
        rot_z = np.array([
            [math.cos(g), -math.sin(g), 0],
            [math.sin(g), math.cos(g), 0],
            [0, 0, 1]
        ])
        
        rotation_matrix = rot_z @ rot_y @ rot_x
        return rotation_matrix
    
    def generate_edges(self):
        points = self.generate_points()
        edges = []
        
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]
            
            edges.append((start_point, end_point))
        
        return edges
        
    @classmethod
    def from_dict(cls, data):
        return cls(data['radius'], data['x_c'], data['y_c'], data['z_c'], data['x_ang'], data['y_ang'], data['z_ang'], data['segments'])

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
        rotation_x = np.array([
            [1, 0, 0],
            [0, math.cos(self.angle_x), -math.sin(self.angle_x)],
            [0, math.sin(self.angle_x), math.cos(self.angle_x)]
        ])
        
        rotation_y = np.array([
            [math.cos(self.angle_y), 0, math.sin(self.angle_y)],
            [0, 1, 0],
            [-math.sin(self.angle_y), 0, math.cos(self.angle_y)]
        ])
        
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
    
def draw_line(screen, start_point, end_point, camera, color, screen_origin_x, screen_origin_y):
    x_1, y_1 = camera.project_point(start_point)
    x_2, y_2 = camera.project_point(end_point)
    x_1 += screen_origin_x
    x_2 += screen_origin_x
    y_1 += screen_origin_y
    y_2 += screen_origin_y
    pygame.draw.line(screen, color, (x_1, y_1), (x_2, y_2), 5)

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

        #draw lines
        draw_line(screen, (0,0,0), (50,0,0), camera, RED, WIDTH/8, 7*HEIGHT/8)
        draw_line(screen, (0,0,0), (0,50,0), camera, BLUE, WIDTH/8, 7*HEIGHT/8)
        draw_line(screen, (0,0,0), (0,0,50), camera, GREEN, WIDTH/8, 7*HEIGHT/8)
        draw_line(screen, (0,100,0), (0,150,0), camera, LIGHT_GRAY, WIDTH/2, HEIGHT/2)

        # Update display
        pygame.display.flip()
        clock.tick(MAX_FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
