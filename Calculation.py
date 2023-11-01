import numpy as np


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Element:
    def __init__(self, node_i, node_j, cross_section_area, youngs_modulus):
        self.node_i = node_i
        self.node_j = node_j
        self.cross_section_area = cross_section_area
        self.youngs_modulus = youngs_modulus
        self.k_local = []
        self.k_global = []
        self.length = 0

    def calculate_element_matrices(self):
        delta_x = self.node_j.x - self.node_i.x
        delta_y = self.node_j.y - self.node_i.y
        self.length = np.sqrt(delta_x**2 + delta_y**2)

        cos_theta = delta_x / self.length
        sin_theta = delta_y / self.length

        self.k_local = (self.cross_section_area * self.youngs_modulus / self.length) * np.array([
            [1, 0, -1, 0],
            [0, 0, 0, 0],
            [-1, 0, -1, 0],
            [0, 0, 0, 0]
        ])

        # Transformation matrix
        transformation_matrix = np.array([
            [cos_theta, sin_theta, 0, 0],
            [-sin_theta, cos_theta, 0, 0],
            [0, 0, cos_theta, sin_theta],
            [0, 0, -sin_theta, cos_theta]
        ])

        self.k_global = transformation_matrix @ self.k_local @ np.transpose(transformation_matrix)

        return self.k_global
