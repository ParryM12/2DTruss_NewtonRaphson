"""
#######################################################################
LICENSE INFORMATION
This file is part of Truss FEM.

Truss FEM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Truss FEM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Truss FEM. If not, see <https://www.gnu.org/licenses/>.
#######################################################################

#######################################################################
Description:
Main file for calculation
#######################################################################
"""

import numpy as np
from typing import Dict
from scipy.sparse import csr_array
import copy


# Define static function to calculate stresses
def sigma(eps, lin_coeff, quad_coeff, e_mod, eps_f):
    # Handle division by zero in eps / abs(eps)
    sign_eps = np.sign(eps)
    sign_eps[eps == 0] = 1  # convention for zero

    # Conditions
    condlist = [(np.abs(eps) <= eps_f) | (quad_coeff == 0), (np.abs(eps) > eps_f) & (quad_coeff > 0)]

    # Choice list for corresponding conditions
    choicelist = [
        (lin_coeff * eps - sign_eps * quad_coeff * eps ** 2) * e_mod,
        (lin_coeff * eps_f - sign_eps * quad_coeff * eps_f ** 2) * e_mod
    ]

    # Element-wise selection of output
    sigma_vals = np.select(condlist, choicelist, default=0)  # default value if none of the conditions are met

    return sigma_vals


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
        sin_theta = - delta_y / self.length

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

        return self.k_local, self.k_global, self.transformation_matrix, self.length


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
        self.displacements_local = []
        self.displacements_cor_total = None
        self.axial_forces_cor = None
        self.f_vec_mismatch = None
        self.node_equilibrium_linear = None
        self.node_equilibrium_nonlinear = None
        self.iter_break_number = 0
        self.e_linalg = None
        self.spring_index = []

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
        k_sys = k_sys.toarray()
        self.spring_index = np.zeros(k_sys.shape[0]).reshape(-1,1)
        # Assemble boundary conditions (supports/springs), if spring stiffness = 1 a rigid bc is applied
        for support_id, support_values in self.supports.items():
            try:
                index_nodes = self.node_to_index[support_values['sup_node']]
            except KeyError:
                print(f"The support {support_id} with the coordinates {support_values['sup_node']} is not connected "
                      f"to a truss element!")
                break
            if support_values['c_x'] > 1:
                k_sys[index_nodes * 2, index_nodes * 2] += support_values['c_x']
                self.spring_index[index_nodes * 2] = support_values['c_x']
            elif support_values['c_x'] == 1:
                k_sys[index_nodes * 2, :] = 0
                k_sys[:, index_nodes * 2] = 0
                k_sys[index_nodes * 2, index_nodes * 2] = 1
            if support_values['c_y'] > 1:
                k_sys[index_nodes * 2 + 1, index_nodes * 2 + 1] += support_values['c_y']
                self.spring_index[index_nodes * 2 + 1] = support_values['c_y']
            elif support_values['c_y'] == 1:
                k_sys[index_nodes * 2 + 1, :] = 0
                k_sys[:, index_nodes * 2 + 1] = 0
                k_sys[index_nodes * 2 + 1, index_nodes * 2 + 1] = 1

        # Return global stiffness matrix
        return k_sys

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
        ele_area = []
        ele_e = []
        ele_lin_coeff = []
        ele_quad_coeff = []
        ele_eps_f = []
        for ele_id, ele_values in self.elements.items():
            ele_id = int(ele_id)
            ele_e.append(ele_values['ele_E'] * 10 ** 3)  # unit conversion MPa -> kN/m²
            ele_area.append(ele_values['ele_A'] * 10 ** -4)  # unit conversion cm² -> m²
            ele_node_i = ele_values['ele_node_i']
            ele_node_j = ele_values['ele_node_j']
            ele_lin_coeff.append(ele_values['ele_lin_coeff'])
            ele_quad_coeff.append(ele_values['ele_quad_coeff'])
            ele_eps_f.append(ele_values['ele_eps_f'])
            # Find the global index for node_i and node_j
            dofs = np.append([self.node_to_index[ele_node_i] * 2, self.node_to_index[ele_node_i] * 2 + 1],
                             [self.node_to_index[ele_node_j] * 2, self.node_to_index[ele_node_j] * 2 + 1])
            element_k_local, element_k_global, element_transformation, length = Element(ele_node_i, ele_node_j,
                                                                                        ele_area[ele_id],
                                                                                        ele_e[
                                                                                            ele_id]).calculate_element_matrices()
            self.element_matrices.append({'DOFs': dofs, 'K_local': element_k_local, 'K_global': element_k_global,
                                          'transformation_matrix': element_transformation, 'length': length})

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
        # Set force vector entries to 0 at the positions of supports
        self.f_vec[np.diag(self.k_sys) == 1] = 0

        # Solve system of equations for global node displacements
        try:
            self.displacements = np.linalg.solve(self.k_sys, self.f_vec)
        except Exception as e:
            self.e_linalg = e
            print(f"An error occurred while solving the system of equations: {self.e_linalg}.")
            return
        # Calculate axial forces and strain
        strain = []
        internal_f_vec_glob = np.zeros(self.f_vec.shape)
        for i in range(len(self.element_matrices)):
            self.displacements_local.append(np.transpose(self.element_matrices[i]['transformation_matrix'])
                                            @ self.displacements[self.element_matrices[i]['DOFs']])
            axial_force_i = self.element_matrices[i]['K_local'] @ self.displacements_local[i]
            axial_force_global_i = self.element_matrices[i]['transformation_matrix'] @ axial_force_i
            self.axial_forces = np.append(self.axial_forces, axial_force_i[2])
            strain.append((self.displacements_local[i][2] - self.displacements_local[i][0])
                          / self.element_matrices[i]['length'])
            internal_f_vec_glob[self.element_matrices[i]['DOFs']] += axial_force_global_i
        # Calculate global forces equilibrium to get support reactions
        self.node_equilibrium_linear = self.f_vec - internal_f_vec_glob

        # Newton-Raphson-Method for nonlinear stress-strain relationship
        displacements_cor = np.zeros((self.k_sys.shape[0], 1))
        strain = np.array(strain).reshape(-1, 1)
        ele_lin_coeff = np.array(ele_lin_coeff).reshape(-1, 1)
        ele_quad_coeff = np.array(ele_quad_coeff).reshape(-1, 1)
        ele_e = np.array(ele_e).reshape(-1, 1)
        ele_area = np.array(ele_area).reshape(-1, 1)
        ele_eps_f = np.array(ele_eps_f).reshape(-1, 1)
        # if self.calc_param['calc_method'] in 'NR' or 'modNR' and sum(ele_quad_coeff) != 0:
        if (self.calc_param['calc_method'] in 'NR' or self.calc_param['calc_method'] in 'modNR') and sum(
                ele_quad_coeff) != 0:
            self.displacements_cor_total = self.displacements
            if self.calc_param['number_of_iterations'] < 1:
                print('The number of iterations has to be ≥ 1. "number_of_iterations" is set to 1.')
                self.calc_param['number_of_iterations'] = 1
            for iter_number in range(1, self.calc_param['number_of_iterations'] + 1):
                # Update axial forces and stiffness (stiffness is constant in the modified Newton-Raphson method)
                axial_forces_cor = sigma(strain, ele_lin_coeff, ele_quad_coeff, ele_e, ele_eps_f) * ele_area

                # Calculate mismatch in node equilibrium
                f_vec_cor = np.zeros(self.f_vec.shape)
                for i in range(len(self.element_matrices)):
                    axial_forces_cor_glob = (self.element_matrices[i]['transformation_matrix'] @
                                             np.array([-axial_forces_cor[i][0], 0, axial_forces_cor[i][0], 0]).reshape(
                                                 4, 1))
                    f_vec_cor[self.element_matrices[i]['DOFs']] += axial_forces_cor_glob
                spring_reactions_forces = self.spring_index * self.displacements_cor_total
                self.f_vec_mismatch = self.f_vec - f_vec_cor
                node_equilibrium = copy.copy(self.f_vec_mismatch)
                self.f_vec_mismatch += - spring_reactions_forces
                # Calculate additional displacements
                if self.calc_param['calc_method'] in 'NR':
                    for i in range(len(self.element_matrices)):
                        ele_e_cor = (ele_lin_coeff + 2 * ele_quad_coeff * strain) * ele_e
                        element_k_local, element_k_global, element_transformation, length \
                            = (Element(self.elements[str(i)]['ele_node_i'], self.elements[str(i)]['ele_node_j'],
                                       ele_area[i], ele_e_cor[i]).calculate_element_matrices())
                        self.element_matrices[i]['K_global'] = element_k_global
                    # Assemble global stiffness matrix
                    self.k_sys = self.assembly_system_matrix()

                # Reduce load vector and check stop criterion
                rows_to_zero = np.diag(self.k_sys) == 1
                self.f_vec_mismatch[rows_to_zero] = 0
                stop_criterion = self.calc_param['delta_f_max']
                if max(abs(self.f_vec_mismatch)) <= stop_criterion:
                    print(f'Stop criterion of Δf ≤ {stop_criterion} kN reached at iteration step {iter_number}!')
                    self.iter_break_number = iter_number
                    self.node_equilibrium_nonlinear = node_equilibrium
                    break

                # Calculate total displacement
                displacements_cor = displacements_cor + np.linalg.solve(self.k_sys, self.f_vec_mismatch)
                self.displacements_cor_total = self.displacements + displacements_cor
                # Update strain and axial forces
                for i in range(len(self.element_matrices)):
                    self.displacements_local[i] = (np.transpose(self.element_matrices[i]['transformation_matrix'])
                                                   @ self.displacements_cor_total[self.element_matrices[i]['DOFs']])
                    strain[i] = ((self.displacements_local[i][2] - self.displacements_local[i][0])
                                 / self.element_matrices[i]['length'])
                self.axial_forces_cor = np.array(sigma(strain, ele_lin_coeff, ele_quad_coeff, ele_e, ele_eps_f)
                                                 * ele_area)
                if iter_number == self.calc_param['number_of_iterations']:
                    print(f'Maximum number of {iter_number} iterations reached without meeting the stop criterion'
                          f' Δf ≤ {stop_criterion} kN!')
                    self.iter_break_number = self.calc_param['number_of_iterations']
        elif 'NR' in self.calc_param['calc_method'] or 'modNR' in self.calc_param['calc_method'] and sum(
                ele_quad_coeff) == 0:
            self.axial_forces_cor = self.axial_forces
            print(f'Attention: You selected a nonlinear Newton-Raphson calculation, '
                  f'but you set the nonlinear parameter β of all elements to 0! Calculating linear...')
        elif 'linear' in self.calc_param['calc_method'] and sum(ele_quad_coeff) != 0:
            print(f'Attention: You selected a linear calculation, '
                  f'but you set the nonlinear parameter β of at least one element not to 0! Calculating linear...')
        # Flatten the list of lists into a single list and change shape of cor_displacements
        self.axial_forces_cor = [force[0] for force in self.axial_forces_cor if force]
        self.displacements_cor_total = self.displacements_cor_total.reshape(-1, 2)
        # Round output
        self.axial_forces = np.round(self.axial_forces, 2)
        if self.f_vec_mismatch is not None:
            self.f_vec_mismatch = np.round(self.f_vec_mismatch, 2)
        if self.axial_forces_cor is not None:
            self.axial_forces_cor = np.round(self.axial_forces_cor, 2)
        if self.node_equilibrium_linear is not None:
            self.node_equilibrium_linear = np.round(self.node_equilibrium_linear, 2)
        if self.node_equilibrium_nonlinear is not None:
            self.node_equilibrium_nonlinear = np.round(self.node_equilibrium_nonlinear, 2)
        # Return solution
        self.solution = {'nodes': self.nodes, 'node_displacements_linear': self.displacements.reshape(-1, 2),
                         'node_displacements_nonlinear': self.displacements_cor_total,
                         'axial_forces_linear': self.axial_forces,
                         'axial_forces_nonlinear': self.axial_forces_cor,
                         'node_equilibrium_linear': self.node_equilibrium_linear,
                         'node_equilibrium_nonlinear': self.node_equilibrium_nonlinear,
                         'node_forces_mismatch': self.f_vec_mismatch,
                         'iteration_break_number': self.iter_break_number,
                         'error_linalg': self.e_linalg}


# Example for testing and debugging
if __name__ == "__main__":
    elements = {'0': {'ele_number': 0,
                      'ele_node_i': (0., 4.),
                      'ele_node_j': (4., 4.),
                      'ele_A': 2000.,
                      'ele_E': 30000.,
                      'ele_lin_coeff': 1.,
                      'ele_quad_coeff': 0.,
                      'ele_eps_f': 2.5e-3},
                '1': {'ele_number': 1,
                      'ele_node_i': (0., 0.),
                      'ele_node_j': (4., 4.),
                      'ele_A': 500.,
                      'ele_E': 30000.,
                      'ele_lin_coeff': 1.,
                      'ele_quad_coeff': 200.,
                      'ele_eps_f': 2.5e-3},
                '2': {'ele_number': 2,
                      'ele_node_i': (4., 4.),
                      'ele_node_j': (5., 0.),
                      'ele_A': 500.,
                      'ele_E': 30000.,
                      'ele_lin_coeff': 1.,
                      'ele_quad_coeff': 200.,
                      'ele_eps_f': 2.5e-3},
                }

    supports = {'0': {'sup_number': 0,
                      'sup_node': (0., 4.),
                      'c_x': 1.,
                      'c_y': 1.},
                '1': {'sup_number': 1,
                      'sup_node': (0., 0.),
                      'c_x': 1.,
                      'c_y': 1.},
                '2': {'sup_number': 2,
                      'sup_node': (5., 0.),
                      'c_x': 1.,
                      'c_y': 1.}
                }

    forces = {'0': {'force_number': 0,
                    'force_node': (4., 4.),
                    'f_x': 0.,
                    'f_y': 1200.}}

    calc_param = {'calc_method': 'NR',
                  'number_of_iterations': 2,
                  'delta_f_max': 1}

    calc = Calculation(elements, supports, forces, calc_param)
    solution = calc.return_solution()
    print('The axial forces of the linear elastic calculation are:')
    print(solution['axial_forces_linear'])
    # if calc_param['calc_method'] in 'NR' or 'modNR':
    if 'NR' in calc_param['calc_method'] or 'modNR' in calc_param['calc_method']:
        print('The axial forces of the nonlinear elastic / ideal plastic calculation are:')
        print(solution['axial_forces_nonlinear'].reshape(1, 3))
