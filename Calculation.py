import numpy as np


class Node:
    """
    The "Node" class contains the (x, y) coordinates of a node.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Element:
    """
    The "Element" class contains the element information (nodes, cross-section, material parameters) and calculates the\n
    element stiffness matrix.
    """

    def __init__(self, node_i, node_j, cross_section_area, youngs_modulus):
        self.node_i = node_i
        self.node_j = node_j
        self.cross_section_area = cross_section_area
        self.youngs_modulus = youngs_modulus
        self.k_local = []
        self.k_global = []
        self.length = 0

    def calculate_element_matrices(self):
        """
        Calculates the local and the global element stiffness matrix.
        :return:
        """
        delta_x = self.node_j.x - self.node_i.x
        delta_y = self.node_j.y - self.node_i.y
        self.length = np.sqrt(delta_x ** 2 + delta_y ** 2)

        cos_theta = delta_x / self.length
        sin_theta = delta_y / self.length

        self.k_local = (self.cross_section_area * self.youngs_modulus / self.length) * np.array([
            [1, 0, -1, 0],
            [0, 0, 0, 0],
            [-1, 0, 1, 0],
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


class Calculation:
    """
    Class for calculating the axial forces and node displacements using the Newton-Raphson method.
    """

    def __init__(self, elements, supports, forces, calculation_param):
        super().__init__(elements, supports, forces, calculation_param)
        self.number_of_elements = []
        self.element_matrices = []
        self.k_glob = np.array([0], dtype=np.float64)
        self.m_glob = np.array([0], dtype=np.float64)
        self.nodes = np.array([0], dtype=np.float64)
        self.solution = {}

    def start_calc(self):
        """Function to start the calculation."""


if "__name__" == "__main__":
    elements = {0: {'ele_number': 0,
                    'ele_node_i': [0, 4],
                    'ele_node_j': [4, 4],
                    'ele_A': 2000,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 0,
                    'ele_eps_f': 2.5e-3},
                1: {'ele_number': 1,
                    'ele_node_i': [0, 0],
                    'ele_node_j': [4, 4],
                    'ele_A': 500,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 200,
                    'ele_eps_f': 2.5e-3},
                2: {'ele_number': 2,
                    'ele_node_i': [4, 4],
                    'ele_node_j': [5, 0],
                    'ele_A': 500,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 200,
                    'ele_eps_f': 2.5e-3},
                }

    calc = Calculation(elements, supports, forces, calculation_param)
    calc.start_calc()
    solution = calc.return_solution()
    print(solution)
