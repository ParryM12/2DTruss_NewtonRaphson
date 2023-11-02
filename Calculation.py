import numpy as np
from typing import Dict
from scipy.sparse import csr_array
import math
from functions.sparse import delete_from_csr


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
        delta_x = self.node_j[0] - self.node_i[0]
        delta_y = self.node_j[1] - self.node_i[1]
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

        return self.k_local, self.k_global


class Calculation:
    """
    Class for calculating the axial forces and node displacements using the Newton-Raphson method.
    """

    def __init__(self, elements: Dict, supports: Dict, forces: Dict, calc_param: Dict):
        self.elements = elements
        self.supports = supports
        self.forces = forces
        self.calc_param = calc_param
        self.number_of_elements = []
        self.element_matrices = []
        self.k_glob = np.array([0], dtype=np.float64)
        self.nodes = np.array([0], dtype=np.float64)
        self.solution = {}

    def return_solution(self):
        """
        Returns the solution as a dictionary.
        :return:
        """
        self.start_calc()
        return self.solution

    def assembly_system_matrix(self):
        """
        Calculates element matrices for every section, assembly system
        :return:
        """

        num_elem = len(self.element_matrices)
        # Pre-allocate lists for sparse matrix data.
        # i_g and j_g are used to index the global matrices
        # k_g and m_g will contain the element matrices in vector format
        i_g = []
        j_g = []
        k_g = []
        num_dofs = 0

        # Convert the element stiffness and mass matrices to vector format (k_g and m_g) and define the corresponding
        # indices i_g and j_g in the global mass/stiffness matrix
        for i in range(num_elem):
            dof_i = self.element_matrices[i]['DOFs']
            k_i = self.element_matrices[i]['K']
            dof_i_len = len(dof_i)
            mesh1, mesh2 = np.meshgrid(range(dof_i_len), range(dof_i_len), indexing='ij')
            ii = mesh1.ravel()
            jj = mesh2.ravel()
            i_g.extend(dof_i[ii])
            j_g.extend(dof_i[jj])
            k_g.extend(k_i.ravel())
            max_dof_i = max(dof_i)
            num_dofs = max(num_dofs, max_dof_i)

        # Create sparse matrices for K and M
        k_glob = csr_array((k_g, (np.array(i_g) - 1, np.array(j_g) - 1)), shape=(num_dofs, num_dofs), dtype=np.float64)
        dof_isnot_zero = list(range(k_glob.shape[0]))
        # Assemble springs  and boundary conditions
        # Assemble stiff boundary conditions
        k_glob = delete_from_csr(k_glob, row_indices=[2, 5], col_indices=[2, 5])
        dof_is_zero = [2, 5]
        # Assemble elastic boundary conditions (springs), if spring stiffness = 1 a rigid bc is applied
        if self.springs['base_phiy'] != 0:
            k_glob[3, 3] += self.springs['base_phiy']
        else:
            k_glob = delete_from_csr(k_glob, row_indices=[3], col_indices=[3])
            dof_is_zero.append(4)
        # Assemble vector to reassemble boundary conditions
        dof_is_zero.sort()
        self.dof_isnot_zero = [item for item in dof_isnot_zero if item not in dof_is_zero]
        # Return global stiffness and mass matrix
        k_glob = round(0.5 * (k_glob + np.transpose(k_glob)), 3)
        # Return as dense matrices if problem is small, else sparse
        # TODO: Test at which number of dofs it is more efficient to use sparse matrices
        if k_glob.shape[0] > 30000:
            return k_glob
        elif k_glob.shape[0] <= 30000:
            return k_glob.todense()

    def solve_system(self):
        """
        Solves the system of equations and returns the axial forces and node displacements.
        :return:
        """
        # Solve the system of equations

    def start_calc(self):
        """Function to start the calculation."""
        # Calculate element stiffness matrices
        for ele_id, ele_values in self.elements.items():
            ele_id = int(ele_id)
            ele_e = ele_values['ele_E'] * 10 ** 3  # unit conversion MPa -> kN/m²
            ele_area = ele_values['ele_A'] * 10 ** -4  # unit conversion cm² -> m²
            ele_node_i = ele_values['ele_node_i']
            ele_node_j = ele_values['ele_node_j']
            ele_lin_coeff = ele_values['ele_lin_coeff']
            ele_quad_coeff = ele_values['ele_quad_coeff']
            ele_eps_f = ele_values['ele_eps_f']
            self.nodes = np.append(self.nodes, [ele_node_i, ele_node_j])
            element_k_local, element_k_global = Element(ele_node_i, ele_node_j,
                                                        ele_area, ele_e).calculate_element_matrices()
            self.element_matrices.append({'DOFs': 0, 'K_local': element_k_local, 'K_global': element_k_global})
        # Construct connectivity between local and global nodes
            self.nodes = np.unique(self.nodes, axis=0)


# Example for testing and debugging
if __name__ == "__main__":
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

    supports = {0: {'sup_number': 0,
                    'sup_node': [0, 4],
                    'c_x': 1,
                    'c_y': 1},
                1: {'sup_number': 1,
                    'sup_node': [0, 0],
                    'c_x': 1,
                    'c_y': 1},
                2: {'sup_number': 2,
                    'sup_node': [5, 0],
                    'c_x': 1,
                    'c_y': 1}
                }

    forces = {0: {'force_number': 0,
                  'force_node': [4, 4],
                  'f_x': 0,
                  'f_y': 1200}}

    calc_param = {'calc_method': 'linear',
                  'number_of_iterations': 0,
                  'delta_f_max': 1}

    calc = Calculation(elements, supports, forces, calc_param)
    calc.start_calc()
    solution = calc.return_solution()
    print(solution)
