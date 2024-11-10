import math
import numpy as np
import json
from scipy.constants import Boltzmann

pressure = 0
chamber_radius = 500

class Particle:
    def __init__(self, diameter, mass):
        self.diamter = diameter # in angstroms
        self.mass = mass # in kg

def mean_free_path(t, p, d):
    """
    t = temperature [Kelvin]
    p = pressure [Pascals]
    d = gas molecule diameter [Angstroms]
    mean free parth [meters]
    """
    return (Boltzmann * t) / (math.pi * math.sqrt(2) * (d**2) * p)

def collision_frequency(l, v):
    """
    l = mean free path [meters]
    v = velocity of particle [m/s]
    collision frequency [1/s]
    """
    return v / l