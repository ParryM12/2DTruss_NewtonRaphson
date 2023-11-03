import numpy as np
from typing import Dict
from scipy.sparse import csr_array


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
        self.transformation_matrix = []

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
        self.transformation_matrix = np.array([
            [cos_theta, sin_theta, 0, 0],
            [-sin_theta, cos_theta, 0, 0],
            [0, 0, cos_theta, sin_theta],
            [0, 0, -sin_theta, cos_theta]
        ])

        self.k_global = self.transformation_matrix @ self.k_local @ np.transpose(self.transformation_matrix)

        return self.k_local, self.k_global, self.transformation_matrix


class Calculation:
    """
    Class for calculating the axial forces and node displacements using the Newton-Raphson method.
    """

    def __init__(self, elements: Dict, supports: Dict, forces: Dict, calc_param: Dict):
        self.elements = elements
        self.supports = supports
        self.forces = forces
        self.calc_param = calc_param
        self.element_matrices = []
        self.k_sys = np.array([0], dtype=np.float64)
        self.nodes = []
        self.solution = {}
        self.node_to_index = []
        self.f_vec = []
        self.displacements = []
        self.axial_forces = np.arange(0)
        self.num_elem = []

    def return_solution(self):
        """
        Returns the solution as a dictionary.
        :return:
        """
        self.start_calc()
        return self.solution

    def assembly_system_matrix(self):
        """
       Assemble global system stiffness matrix
        :return:
        """

        self.num_elem = len(self.element_matrices)
        # Pre-allocate lists for sparse matrix data.
        # i_g and j_g are used to index the global matrices
        # k_g and m_g will contain the element matrices in vector format
        i_g = []
        j_g = []
        k_g = []
        num_dofs = 0

        # Convert the element stiffness and mass matrices to vector format (k_g and m_g) and define the corresponding
        # indices i_g and j_g in the global mass/stiffness matrix
        for i in range(self.num_elem):
            dof_i = self.element_matrices[i]['DOFs']
            k_i = self.element_matrices[i]['K_global']
            dof_i_len = len(dof_i)
            mesh1, mesh2 = np.meshgrid(range(dof_i_len), range(dof_i_len), indexing='ij')
            ii = mesh1.ravel()
            jj = mesh2.ravel()
            i_g.extend(dof_i[ii])
            j_g.extend(dof_i[jj])
            k_g.extend(k_i.ravel())
            max_dof_i = max(dof_i)
            num_dofs = max(num_dofs, max_dof_i)

        # Create sparse matrix for K
        k_sys = csr_array((k_g, (np.array(i_g), np.array(j_g))), shape=(num_dofs + 1, num_dofs + 1), dtype=np.float64)

        # Assemble boundary conditions (supports/springs), if spring stiffness = 1 a rigid bc is applied
        for support_id, support_values in self.supports.items():
            try:
                index_nodes = self.node_to_index[support_values['sup_node']]
            except KeyError:
                print(f"The support {support_id} with the coordinates {support_values['sup_node']} is not connected "
                      f"to a truss element!")
                break
            if support_values['c_x'] != 1:
                k_sys[index_nodes * 2, index_nodes * 2] += support_values['c_x']
            elif support_values['c_x'] == 1:
                k_sys[index_nodes * 2, :] = 0
                k_sys[:, index_nodes * 2] = 0
                k_sys[index_nodes * 2, index_nodes * 2] = 1
            if support_values['c_y'] != 1:
                k_sys[index_nodes * 2 + 1, index_nodes * 2 + 1] += support_values['c_y']
            elif support_values['c_y'] == 1:
                k_sys[index_nodes * 2 + 1, :] = 0
                k_sys[:, index_nodes * 2 + 1] = 0
                k_sys[index_nodes * 2 + 1, index_nodes * 2 + 1] = 1

        # Return global stiffness matrix
        return k_sys.todense()

    def start_calc(self):
        """Function to start the calculation."""
        # Create global node list
        for element in self.elements.values():
            # Check and add nodes to the list if they are not already in it
            if element['ele_node_i'] not in self.nodes:
                self.nodes.append(element['ele_node_i'])
            if element['ele_node_j'] not in self.nodes:
                self.nodes.append(element['ele_node_j'])

        # Create a mapping from node tuples to their index in the global_nodes_list
        self.node_to_index = {node: index for index, node in enumerate(self.nodes)}

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
            # Find the global index for node_i and node_j
            dofs = np.append([self.node_to_index[ele_node_i] * 2, self.node_to_index[ele_node_i] * 2 + 1],
                             [self.node_to_index[ele_node_j] * 2, self.node_to_index[ele_node_j] * 2 + 1])
            element_k_local, element_k_global, element_transformation = Element(ele_node_i, ele_node_j, ele_area,
                                                                                ele_e).calculate_element_matrices()
            self.element_matrices.append({'DOFs': dofs, 'K_local': element_k_local, 'K_global': element_k_global,
                                          'transformation_matrix': element_transformation})

        # Assemble global stiffness matrix
        self.k_sys = self.assembly_system_matrix()

        # Assemble global load vector
        self.f_vec = np.zeros((self.k_sys.shape[0], 1))
        for force_id, force_values in self.forces.items():
            try:
                index_nodes = self.node_to_index[force_values['force_node']]
            except KeyError:
                print(f"The force {force_id} with the coordinates {force_values['force_node']} is not connected "
                      f"to a truss element!")
                break
            self.f_vec[index_nodes * 2] += force_values['f_x']
            self.f_vec[index_nodes * 2 + 1] += force_values['f_y']

        # Solve system of equations for global node displacements
        self.displacements = np.linalg.solve(self.k_sys, self.f_vec)

        # Calculate axial forces
        for i in range(len(self.element_matrices)):
            displacements_local = (np.transpose(self.element_matrices[i]['transformation_matrix'])
                                   @ self.displacements[self.element_matrices[i]['DOFs']])
            axial_force_i = self.element_matrices[i]['K_local'] @ displacements_local
            self.axial_forces = np.append(self.axial_forces, axial_force_i[2])

        # Return solution
        self.solution = {'node_displacements': self.displacements, 'axial_foces': self.axial_forces}


# Example for testing and debugging
if __name__ == "__main__":
    elements = {0: {'ele_number': 0,
                    'ele_node_i': (0, 4),
                    'ele_node_j': (4, 4),
                    'ele_A': 2000,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 0,
                    'ele_eps_f': 2.5e-3},
                1: {'ele_number': 1,
                    'ele_node_i': (0, 0),
                    'ele_node_j': (4, 4),
                    'ele_A': 500,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 200,
                    'ele_eps_f': 2.5e-3},
                2: {'ele_number': 2,
                    'ele_node_i': (4, 4),
                    'ele_node_j': (5, 0),
                    'ele_A': 500,
                    'ele_E': 30000,
                    'ele_lin_coeff': 1,
                    'ele_quad_coeff': 200,
                    'ele_eps_f': 2.5e-3},
                }

    supports = {0: {'sup_number': 0,
                    'sup_node': (0, 4),
                    'c_x': 1,
                    'c_y': 1},
                1: {'sup_number': 1,
                    'sup_node': (0, 0),
                    'c_x': 1,
                    'c_y': 1},
                2: {'sup_number': 2,
                    'sup_node': (5, 0),
                    'c_x': 1,
                    'c_y': 1}
                }

    forces = {0: {'force_number': 0,
                  'force_node': (4, 4),
                  'f_x': 0,
                  'f_y': 1200}}

    calc_param = {'calc_method': 'linear',
                  'number_of_iterations': 0,
                  'delta_f_max': 1}

    calc = Calculation(elements, supports, forces, calc_param)
    solution = calc.return_solution()
    print(solution)
