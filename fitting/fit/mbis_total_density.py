from __future__ import division
from mbis_abc import MBIS_ABC
import numpy as np

class TotalMBIS(MBIS_ABC):
    def __init__(self, element_name, atomic_number, grid_obj, electron_density, weights=None):
        super(TotalMBIS, self).__init__(element_name, atomic_number, grid_obj, electron_density, weights=weights)

    def get_normalized_coefficients(self, coeff_arr, exp_arr):
        normalized_constants = self.get_all_normalization_constants(exp_arr)
        assert len(normalized_constants) == len(coeff_arr)
        norm_coeff_arr = coeff_arr * normalized_constants
        assert norm_coeff_arr.ndim == 1
        assert len(norm_coeff_arr) == len(coeff_arr) == len(exp_arr)
        assert norm_coeff_arr[0] == coeff_arr[0] * normalized_constants[0], "Instead we get %r and %r * %r" %(norm_coeff_arr[0],
                                                                                                         coeff_arr[0],
                                                                                                         normalized_constants[0])
        return coeff_arr * normalized_constants

    def get_normalized_gaussian_density(self, coeff_arr, exp_arr):
        exponential = np.exp(-exp_arr * np.power(self.grid_points, 2.))
        assert exponential.shape == (len(self.grid_points), len(exp_arr))
        normalized_coeffs = self.get_normalized_coefficients(coeff_arr, exp_arr)
        assert normalized_coeffs.ndim == 1.
        normalized_gaussian_density = np.dot(exponential, normalized_coeffs)
        index_where_zero_occurs = np.where(normalized_gaussian_density == 0.)
        if len(index_where_zero_occurs[0]) != 0:
            normalized_gaussian_density[index_where_zero_occurs] = \
                    normalized_gaussian_density[index_where_zero_occurs[0][0] - 1]
        return normalized_gaussian_density

    def get_integration_factor(self, exponent, masked_normed_gaussian, upt_exponent=False):
        ratio = self.masked_electron_density / masked_normed_gaussian
        assert not np.all(masked_normed_gaussian == 0.)
        assert not np.all(np.array([0., 0., 0., 1.]) == 0.)
        assert not np.all(ratio == 0.)
        assert ratio.ndim == 1.
        integrand = ratio * np.ma.asarray(np.exp(-exponent * self.masked_grid_squared))
        assert integrand.ndim == 1.
        assert not np.all(integrand == 0.), "Exponent is %r " % exponent
        if upt_exponent:
            integrand = self.weights * integrand * self.masked_grid_squared
            return(self.get_normalization_constant(exponent) *\
                   self.grid_obj.integrate(integrand))
        previous_int = integrand.copy()
        integrand = self.weights * integrand
        #integrand = integrand * self.weights

        return self.get_normalization_constant(exponent) *\
               self.grid_obj.integrate(integrand)

    def update_coefficients(self, coeff_arr, exp_arr):
        #assert np.all(coeff_arr > 0), "Coefficients should be positive. Instead we got %r" % coeff_arr
        assert np.all(exp_arr > 0), "Exponents should be positive. Instead we got %r" % exp_arr
        masked_normed_gaussian = np.ma.asarray(self.get_normalized_gaussian_density(coeff_arr, exp_arr))
        assert masked_normed_gaussian.ndim == 1.
        new_coeff = coeff_arr.copy()
        for i in range(0, len(coeff_arr)):
            new_coeff[i] *= self.get_integration_factor(exp_arr[i], masked_normed_gaussian)
            new_coeff[i] /= self.lagrange_multiplier
        assert np.all(coeff_arr != np.inf)
        assert np.all(exp_arr != np.inf)
        return new_coeff

    def update_exponents(self, coeff_arr, exp_arr, with_convergence=True):
        #assert np.all(coeff_arr > 0), "Coefficients should be positive. Instead we got %r" % coeff_arr
        assert np.all(exp_arr > 0), "Exponents should be positive. Instead we got %r" % exp_arr
        masked_normed_gaussian = np.ma.asarray(self.get_normalized_gaussian_density(coeff_arr, exp_arr)).copy()

        new_exps = exp_arr.copy()
        for i in range(0, len(exp_arr)):
            if with_convergence:
                new_exps[i] = 3. * self.lagrange_multiplier
            else:
                new_exps[i] = 3. * self.get_integration_factor(exp_arr[i], masked_normed_gaussian)
            integration = self.get_integration_factor(exp_arr[i], masked_normed_gaussian, upt_exponent=True)
            #assert integration != 0, "Integration of the integrand is zero."
            if integration == 0.:
                print(coeff_arr, exp_arr)
            assert not np.isnan(integration), "Integration should not be nan"
            new_exps[i] /= ( 2. * integration)
        return new_exps

    def get_normalization_constant(self, exponent):
        return (exponent / np.pi) ** (3./2.)

    def get_new_coeffs_and_old_coeffs(self, coeff_arr, exp_arr):
        new_coeff = self.update_coefficients(coeff_arr, exp_arr)
        return new_coeff, coeff_arr

    def get_new_exps_and_old_exps(self, coeff_arr, exp_arr):
        new_exps = self.update_exponents(coeff_arr, exp_arr)
        return new_exps, exp_arr

    def run(self, threshold_coeff, threshold_exp, coeff_arr, exp_arr, iprint=False, iplot=False):
        # Old Coeffs/Exps are initized this way to allow while loop inequlity to hold initially
        old_coeffs = 2. * coeff_arr.copy() + threshold_coeff * 2.
        new_coeffs = coeff_arr.copy()
        old_exps = 2. * exp_arr.copy() + threshold_exp * 2.
        new_exps = exp_arr.copy()
        storage_of_errors = [["""Integration Using Trapz"""],
                             [""" goodness of fit"""],
                             [""" goof of fit with r^2"""],
                             [""" KL Divergence Formula"""]]
        previous_objective_func = 1e10
        current_objective_func = 1e4
        counter = 0
        while np.any(np.abs(new_exps - old_exps) > threshold_exp ) and np.abs(previous_objective_func - current_objective_func) > 1e-10:
            new_coeffs, old_coeffs = self.get_new_coeffs_and_old_coeffs(new_coeffs, new_exps)

            while np.any(np.abs(old_coeffs - new_coeffs)  > threshold_coeff):
                new_coeffs, old_coeffs = self.get_new_coeffs_and_old_coeffs(new_coeffs, new_exps)

                #if 0. in new_coeffs:
                #    return new_coeffs, new_exps

                model = self.get_normalized_gaussian_density(new_coeffs , new_exps)
                sum_of_coeffs = np.sum(new_coeffs)
                integration_model_four_pi, goodness_of_fit, goodness_of_fit_r_squared, objective_function = \
                        self.get_descriptors_of_model(model)
                if iprint:
                    print(counter, integration_model_four_pi, np.round(sum_of_coeffs), \
                          goodness_of_fit, goodness_of_fit_r_squared, \
                          objective_function,  True, np.max(np.abs(old_coeffs - new_coeffs)),
                          np.max(np.abs(new_coeffs - old_coeffs) / old_coeffs), model[0], self.electron_density[0])
                if iplot:
                    storage_of_errors[0].append(integration_model_four_pi)
                    storage_of_errors[1].append(goodness_of_fit)
                    storage_of_errors[2].append(goodness_of_fit_r_squared)
                    storage_of_errors[3].append(objective_function)
                counter += 1
            new_exps, old_exps = self.get_new_exps_and_old_exps(new_coeffs, new_exps)
            """
            for i, exps in enumerate(new_exps):
                # weights = 1
                print(self.grid_obj.integrate(self.weights * self.masked_electron_density ) / self.atomic_number,
                      (exps / np.pi)**(3./2.) * self.grid_obj.integrate(self.weights * np.exp(-exps * self.masked_grid_squared)))

                #WEIGHTS = 1/ 4 pi r^2
                model = mbis.get_normalized_gaussian_density(new_coeffs, new_exps)
                print(self.grid_obj.integrate(self.masked_electron_density / (4. * np.pi * np.power(self.grid_obj.radii,2.)) /  self.atomic_number),
                      (exps / np.pi) ** (3. / 2.) * self.grid_obj.integrate((self.masked_electron_density / model) * np.exp(-exps * self.masked_grid_squared)
                                                                            / (4. * np.pi * np.power(self.grid_obj.radii,2.)) ),

                      (exps / np.pi) ** (3. / 2.) * self.grid_obj.integrate( np.exp(-exps * self.masked_grid_squared)
                          / (4. * np.pi * np.power(self.grid_obj.radii, 2.))
                          ))

                # WEIGHTS = 1 / 4 pi r
                print(self.grid_obj.integrate(self.masked_electron_density / (4. * np.pi * self.grid_obj.radii) / self.atomic_number),
                      (exps / np.pi) ** (3. / 2.) * self.grid_obj.integrate(np.exp(-exps * self.masked_grid_squared) / (4 * np.pi * self.grid_obj.radii)))
                print("")
            for i, exps in enumerate(new_exps):
                first = (2. / 3.) * (exps**(5./2.) / np.pi **(3./2.) * np.trapz(4. * np.pi * self.weights * np.exp(-exps * np.power(self.grid_obj.radii,2.)) * np.power(self.grid_obj.radii,4.),
                                                                                    x=np.ravel(self.grid_obj.radii)))
                print(first, 1)
            """
            model = self.get_normalized_gaussian_density(new_coeffs, new_exps)
            sum_of_coeffs = np.sum(new_coeffs)
            integration_model_four_pi, goodness_of_fit, goodness_of_fit_r_squared, objective_function = \
                        self.get_descriptors_of_model(model)
            temp_obj = current_objective_func
            current_objective_func = objective_function
            previous_objective_func = temp_obj

            if iprint:
                if counter % 100 == 0.:
                    for x in range(0, len(new_coeffs)):
                        print(new_coeffs[x], new_exps[x])
                print(counter, integration_model_four_pi, np.round(sum_of_coeffs), \
                      goodness_of_fit, goodness_of_fit_r_squared, \
                      objective_function, False, np.max(np.abs(new_exps - old_exps)),
                      np.max(np.abs(new_exps - old_exps) / old_exps), model[0], self.electron_density[0])
            if iplot:
                storage_of_errors[0].append(integration_model_four_pi)
                storage_of_errors[1].append(goodness_of_fit)
                storage_of_errors[2].append(goodness_of_fit_r_squared)
                storage_of_errors[3].append(objective_function)
            counter += 1
        if iplot:
            self.create_plots(storage_of_errors[0], storage_of_errors[1], storage_of_errors[2], storage_of_errors[3])
        return new_coeffs, new_exps

    def check_redundancies(self, coeffs, exps):
        for i, alpha in enumerate(exps):
            indexes_where_they_are_same = []
            for j in range(0, len(exps)):
                if i != j:
                    if np.abs(alpha - exps[j]) < 1e-5:
                        indexes_where_they_are_same.append(j)

            for index in indexes_where_they_are_same:
                coeffs[i] += coeffs[j]
            if len(indexes_where_they_are_same) != 0:
                print("-------- Redundancies found ---------")
                print()
                exps = np.delete(exps, indexes_where_they_are_same)
                coeffs = np.delete(coeffs, indexes_where_they_are_same)
        assert len(exps) == len(coeffs)
        return coeffs, exps

    def run_greedy(self,factor, threshold_coeff, threshold_exps, iprint=False):
        def get_next_possible_coeffs_and_exps(factor, coeffs, exps):
            size = exps.shape[0]
            all_choices_of_exponents = []
            all_choices_of_coeffs = []
            coeff_value=100.
            for index, exp in np.ndenumerate(exps):
                if index[0] == 0:
                    exponent_array = np.insert(exps, index, exp / factor )
                    coefficient_array = np.insert(coeffs, index, coeff_value)
                elif index[0] <= size:
                    exponent_array = np.insert(exps, index, (exps[index[0] - 1] + exps[index[0]])/2)
                    coefficient_array = np.insert(coeffs, index, coeff_value)
                all_choices_of_exponents.append(exponent_array)
                all_choices_of_coeffs.append(coefficient_array)
                if index[0] == size - 1:
                    exponent_array = np.append(exps, np.array([ exp * factor] ))
                    all_choices_of_exponents.append(exponent_array)
                    all_choices_of_coeffs.append(np.append(coeffs, np.array([coeff_value])))
            return all_choices_of_coeffs, all_choices_of_exponents

        #######################################
        ##### SOLVE FOR ONE GAUSSIAN FUNCTION##
        ######################################
        coeffs = np.array([float(self.atomic_number)])
        print(coeffs)
        exps = np.array([0.034])
        coeffs, exps = self.run(1e-4, 1e-3, coeffs, exps, iprint=iprint)
        print("Single Best Coeffs and Exps: ", coeffs, exps)
        #######################################
        ##### ITERATION: NEXT GAUSSIAN FUNCS##
        ######################################
        num_of_functions = 1
        for x in range(0, 30):
            next_coeffs, next_exps = get_next_possible_coeffs_and_exps(factor, coeffs, exps)

            num_of_functions += 1

            best_local_found_objective_func = 1e10
            best_local_coeffs = None
            best_local_exps = None
            for i, exponents in enumerate(next_exps):
                exponents[exponents==0] = 1e-6
                next_coeffs[i][next_coeffs[i] == 0.] = 1e-12
                next_coeffs[i], exps = self.run(10., 1000., next_coeffs[i], exponents, iprint=False)
                objective_func = self.get_objective_function(self.get_normalized_gaussian_density(next_coeffs[i],
                                                                                               exponents))
                if objective_func < best_local_found_objective_func:
                    best_local_found_objective_func = objective_func
                    best_local_coeffs = next_coeffs[i]
                    best_local_exps = exponents

            print(num_of_functions,
                    self.get_descriptors_of_model(self.get_normalized_gaussian_density(best_local_coeffs, best_local_exps)))
            coeffs, exps = best_local_coeffs, best_local_exps
            coeffs, exps = self.run(threshold_coeff, threshold_exps, coeffs, exps, iprint=iprint)

            print(num_of_functions,
                    self.get_descriptors_of_model(self.get_normalized_gaussian_density(coeffs, exps)))
            print()
            coeffs, exps = self.checkFalse_redundancies(coeffs, exps)
            num_of_functions = len(coeffs)


    def get_obj_func_for_optimizing(self, parameters):
        coeffs = parameters[:len(parameters)//2]
        exps = parameters[len(parameters)//2:]
        model = self.get_normalized_gaussian_density(coeffs, exps)
        return self.get_objective_function(model)

    def optimize_using_slsqp(self, parameters):
        from scipy.optimize import minimize
        def constraint(x, *args):
            leng = len(x) // 2
            return np.sum(x[0:leng]) - self.atomic_number

        cons = (  # {'type':'eq','fun':integration_constraint},
            {'type': 'eq', 'fun': constraint})
        bounds = np.array([(0.0, np.inf) for x in range(0, len(parameters))], dtype=np.float64)
        f_min_slsqp = minimize(self.get_obj_func_for_optimizing, x0=parameters, method="SLSQP",
                                              bounds=bounds, constraints=cons,
                                              jac=False,  options={"maxiter": 100000, "disp":True})

        parameters = f_min_slsqp['x']
        print(f_min_slsqp)
        return parameters





if __name__ == "__main__":
    #################
    ## SET UP#######
    ###########
    ATOMIC_NUMBER = 9
    ELEMENT_NAME = "f"
    USE_HORTON = False
    USE_FILLED_VALUES_TO_ZERO = True
    THRESHOLD_COEFF = 1e-2
    THRESHOLD_EXPS = 40
    import os

    current_directory = os.path.dirname(os.path.abspath(__file__))[:-3]
    file_path = current_directory + "data/examples//" + ELEMENT_NAME
    if USE_HORTON:
        import horton
        rtf = horton.ExpRTransform(1.0e-30, 25, 1000)
        radial_grid_2 = horton.RadialGrid(rtf)
        from fitting.density.radial_grid import Horton_Grid
        radial_grid = Horton_Grid(1e-80, 25, 1000, filled=USE_FILLED_VALUES_TO_ZERO)
    else:
        NUMB_OF_CORE_POINTS = 400; NUMB_OF_DIFFUSE_POINTS = 500
        from fitting.density.radial_grid import Radial_Grid
        from fitting.density.atomic_slater_density import Atomic_Density
        radial_grid = Radial_Grid(ATOMIC_NUMBER, NUMB_OF_CORE_POINTS, NUMB_OF_DIFFUSE_POINTS, [50, 75, 100],filled=USE_FILLED_VALUES_TO_ZERO)


    from fitting.density import Atomic_Density
    atomic_density = Atomic_Density(file_path, radial_grid.radii)
    from fitting.fit.GaussianBasisSet import GaussianTotalBasisSet
    atomic_density.electron_density /= ATOMIC_NUMBER
    from fitting.fit.model import Fitting
    atomic_gaussian = GaussianTotalBasisSet(ELEMENT_NAME, np.reshape(radial_grid.radii,
                                                                    (len(radial_grid.radii), 1)), file_path)
    weights = None#(4. * np.pi * radial_grid.radii**1.)#1. / (1 + (4. * np.pi * radial_grid.radii ** 2.))#1. / (4. * np.pi * radial_grid.radii**0.5) #np.exp(-0.01 * radial_grid.radii**2.)

    fitting_obj = Fitting(atomic_gaussian)
    mbis = TotalMBIS(ELEMENT_NAME, 1, radial_grid, atomic_density.electron_density, weights=weights)

    exps = atomic_gaussian.UGBS_s_exponents[:-3]
    coeffs = fitting_obj.optimize_using_nnls(atomic_gaussian.create_cofactor_matrix(exps))
    print(exps)
    coeffs[coeffs == 0.] = 1e-6

    print(radial_grid.integrate(mbis.electron_density))
    print(radial_grid.integrate(mbis.get_normalized_gaussian_density(coeffs, exps)))
    coeffs, exps = mbis.run(1e-2, 1e-1, coeffs, exps, iprint=True)
    #coeffs = np.array([500.])
    #exps = np.array([0.05])

    parameters = mbis.optimize_using_slsqp(np.append(coeffs, exps))
    coeffs, exps = parameters[:len(parameters)//2], parameters[len(parameters)//2:]
    model = mbis.get_normalized_gaussian_density(coeffs, exps)
    print(mbis.get_descriptors_of_model(model), np.abs(model[0] - atomic_density.electron_density[0]))
    coeffs[coeffs == 0.] = 1e-30
    exps[exps==0.] = 1e-30
    import sys
    sys.exit()

    coeffs, exps = mbis.run(THRESHOLD_COEFF, THRESHOLD_EXPS, coeffs, exps, iprint=True)
    #coeffs, exps = mbis.run_greedy(2. , 1e-2, 1e-1, iprint=True)
    print("Final Coeffs, Exps: ", coeffs, exps )


    ##########################
    ##### PLOT ############
    #######################

    from plotting_functions import *
    model = mbis.get_normalized_gaussian_density(coeffs, exps)
    plot_atomic_density(radial_grid.radii, model, atomic_density.electron_density, "Weights - 1/ (1 + 4 pi r^2)", "weights_one_plus_four_pi_rsquared_inv")
    plot_density_sections(atomic_density.electron_density, model, radial_grid.radii, title='weights - 1/ (1 + 4 pi r^2)')
    """
    coeffs = np.array([  5.37392144e-08,   1.43067270e-15,   9.55155646e-16,
                         5.85184393e-08,   8.91743793e-06,   1.51012541e-06,
                         6.75440699e-06,   3.77361749e-06,   2.81295280e-04,
                         1.05047484e-03,   4.57818235e-04,   9.78497372e-03,
                         3.28696365e-02,   6.47375622e-02,   1.52893402e-01,
                         6.40408276e-01,   8.59436347e-01,   3.58250996e-02,
                         7.37241184e-09,   1.18885179e+00,   2.31162944e+00,
                         2.67638300e+00,   9.43193713e-01,   8.21760923e-02])
    exps = np.array([  5.76797592e+05,   5.76797592e+05,   5.76797592e+05,
                     5.76797592e+05,   3.87637212e+04,   3.87637212e+04,
                     3.87637212e+04,   3.87637212e+04,   3.83630934e+03,
                     3.83630934e+03,   3.83630934e+03,   6.16627np.exp(-100. * radial_grid.radii**4)733e+02,
                     6.16627733e+02,   1.93492242e+02,   1.90876217e+02,
                     7.72234427e+01,   3.28170225e+01,   3.28170225e+01,
                     3.28170225e+01,   3.04085648e+00,   1.89568691e+00,
                     9.62126885e-01,   4.64140464e-01,   2.27213679e-01])

    for i in range(0, len(exps)):
        model = mbis.get_normalized_gaussian_density(coeffs, exps)
        print(mbis.get_normalization_constant(exps[i]) * radial_grid.integrate(mbis.masked_electron_density * np.exp(-exps[i] * mbis.masked_grid_squared) / model))
    """