import json
import random
import math
import numpy as np

# Parameters for point generation
num_points = 1  # Number of points to generate
max_radius = 200   # Maximum radius from the origin
lambda_ = 50       # Fall-off rate for density distribution
grid_size = 50     # The size of the grid for density calculation (number of divisions along each axis)
neighbor_radius = 5  # The radius for considering neighbors (local neighborhood for density)

# Function to generate a random point with exponential fall-off
def generate_point():
    # Radial distance based on exponential fall-off
    r = random.expovariate(1 / lambda_)
    if r > max_radius:
        r = max_radius  # Ensure the point stays within the maximum radius

    # Random spherical coordinates
    theta = random.uniform(0, 2 * math.pi)  # Azimuthal angle
    phi = random.uniform(0, math.pi)        # Polar angle

    # Convert spherical coordinates to Cartesian coordinates
    x = r * math.sin(phi) * math.cos(theta)
    y = r * math.sin(phi) * math.sin(theta)
    z = r * math.cos(phi)

    return {"x": x, "y": y, "z": z}

# Function to calculate the distance between two points
def calculate_distance(p1, p2):
    return math.sqrt((p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2 + (p1['z'] - p2['z'])**2)

# Function to calculate the density around each point and determine the color
def calculate_density_and_color(point, all_points, neighbor_radius=neighbor_radius):
    # Count the number of neighbors within the neighbor_radius
    density = 0
    for other_point in all_points:
        if calculate_distance(point, other_point) < neighbor_radius:
            density += 1

    # Normalize the density to control the color intensity
    red_intensity = min(255, density * 10)  # Scale factor for red intensity (density * scale_factor)

    # Color should transition from white (255, 255, 255) to red (255, 0, 0)
    return [255 - red_intensity, 255 - red_intensity, 255]  # White -> Red gradient (R and G decrease as Red increases)

# Generate points
points = [generate_point() for _ in range(num_points)]

# Calculate density and apply color to each point
for point in points:
    point['color'] = calculate_density_and_color(point, points)

# Save points to JSON file
with open("points.json", "w") as file:
    json.dump(points, file, indent=4)

print(f"Generated {num_points} points with density-based gradient colors and saved to 'points_density_gradient.json'")
