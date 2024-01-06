import numpy as np


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
    sigma_vals = np.select(condlist, choicelist, default=0) # default value if none of the conditions are met

    return sigma_vals
