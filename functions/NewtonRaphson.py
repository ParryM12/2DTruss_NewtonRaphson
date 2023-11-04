import numpy as np


def sigma(eps, lin_coeff, quad_coeff, e_mod, eps_f):
    # Conditions
    condlist = [eps <= eps_f, eps > eps_f]

    # Choice list for corresponding conditions
    choicelist = [(lin_coeff * eps + quad_coeff * eps ** 2) * e_mod,
                  (lin_coeff * eps_f + quad_coeff * eps_f ** 2) * e_mod]

    # Element-wise selection of output
    sigma_vals = np.select(condlist, choicelist)

    return sigma_vals
