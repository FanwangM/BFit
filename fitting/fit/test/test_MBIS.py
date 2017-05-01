import numpy as np
import unittest

from fitting.density.atomic_density.atomic_slater_density import Atomic_Density
from fitting.fit.MBIS import update_coefficients, iterative_MBIS_method, measure_error_by_integration_of_difference

from fitting.fit.GaussianBasisSet import GaussianTotalBasisSet
from fitting.fit.model import Fitting


#TODO LIST
#TODO: Error for test_one_coefficient_using_trapz has a really small error

class Default_Setup_For_MBIS(unittest.TestCase):
    def set_up_grid(self):
        ATOMIC_NUMBER = 4
        from fitting.radial_grid.radial_grid import RadialGrid
        radial_grid = RadialGrid(ATOMIC_NUMBER)
        NUMBER_OF_CORE_POINTS = 200; NUMBER_OF_DIFFUSED_PTS = 300
        row_grid_points = radial_grid.grid_points(NUMBER_OF_CORE_POINTS, NUMBER_OF_DIFFUSED_PTS, [50, 75, 100])
        column_grid_points = np.reshape(row_grid_points, (len(row_grid_points), 1))
        return column_grid_points

    def setUp(self):
        file_path = r"C:\Users\Alireza\PycharmProjects\fitting\fitting\data\examples\\be.slater"
        self.grid = self.set_up_grid()
        be = GaussianTotalBasisSet("be", self.grid, file_path)
        self.be = be
        self.fitting_obj = Fitting(be)
        self.electron_density = be.electron_density

        be_atomic_dens = Atomic_Density(file_path, self.grid)
        self.slater_list_of_orbitals = be_atomic_dens.VALUES['orbitals']
        #print(be_atomic_dens.VALUES)
        self.slater_coeffs = be_atomic_dens.all_coeff_matrix('S')
        self.slater_basis_nums = be_atomic_dens.VALUES['basis_numbers']['S']
        self.slater_exps = be_atomic_dens.VALUES['orbitals_exp']['S']
        self.slater_orbitals_electron_array = be_atomic_dens.VALUES['orbitals_electron_array']
        #print(self.slater_coeffs,
        #      self.slater_basis_nums,
        #      self.slater_exps)

class Test_MBIS_For_Coefficients(Default_Setup_For_MBIS):
    def test_updating_one_coefficient_using_trapz(self):
        initial_coefficients = np.array([[5.0], [6.0], [10000.0], [200000.0]])
        constant_exponents = np.array([[20.] , [30.], [0.01], [1.5]])

        for x in range(0, initial_coefficients.shape[0]):
            new_coefficient = update_coefficients(np.array([initial_coefficients[x][0]]),
                                                  np.array([constant_exponents[x][0]]), self.electron_density, self.grid)
            expected_trapz_solution = (constant_exponents[x] / np.pi)**(3/2) *\
                                    np.trapz(y=np.ravel(self.electron_density), x=np.ravel(self.grid))
            assert np.abs(new_coefficient[0] - expected_trapz_solution) < 1e-1

    def test_zero_initial_coefficient(self):
        initial_coefficient = np.array([0.])
        try:
            new_coefficient = update_coefficients(initial_coefficient, np.array([0.]), self.electron_density, self.grid)
        except AssertionError:
            assert True

    def test_updating_two_coefficient_simple_initial_guess(self):
        initial_coefficients = np.array([1., 1.])
        constant_exponents = np.array([1., 2.])
        grid_squared = np.ravel(np.power(self.grid, 2.))
        new_coefficient_1, new_coefficient_2 = update_coefficients(initial_coefficients, constant_exponents, self.electron_density, self.grid)

        #################################
        ## Using Trapz and Masked Array
        #################################

        # First Coefficient
        integrand = np.ravel(self.electron_density) * np.exp(-1. * np.power(np.ravel(self.grid), 2.))
        masked_integrand = np.ma.array(integrand / (np.exp(-1 * grid_squared) + np.exp(-2. * grid_squared)))
        expected_trapz_solution_1 = (1. / np.pi)**(3/2) * np.trapz(y=masked_integrand, x=np.ravel(self.grid))
        print(np.abs(expected_trapz_solution_1 - new_coefficient_1))
        assert np.abs(expected_trapz_solution_1 - new_coefficient_1) < 1e-5

        # Second Coefficient
        integrand_2 = np.ravel(self.electron_density) * np.exp(-2. * grid_squared)
        masked_integrand = np.ma.array(integrand / (np.exp(-1 * grid_squared) + np.exp(-2. * grid_squared)))
        expected_trapz_solution_2 = (2. / np.pi)**(3/2) * np.trapz(y=masked_integrand, x=np.ravel(self.grid))
        print(np.abs(expected_trapz_solution_1 - new_coefficient_1))
        assert np.abs(expected_trapz_solution_2 - new_coefficient_2) < 1.

        #################################
        ## Using Trapz and nan_to_num
        #################################

        # First Coefficient
        integrand = integrand / (np.exp(-1 * grid_squared) + np.exp(-2. * grid_squared))
        integrand_no_nan = np.nan_to_num(integrand)
        expected_trapz_solution_1 = (1. / np.pi)**(3/2) * np.trapz(y=integrand_no_nan, x=np.ravel(self.grid))
        assert np.abs(expected_trapz_solution_1 - new_coefficient_1) < 1e-5

        # Second Coefficient
        integrand_2 = integrand_2 / (np.exp(-1 * grid_squared) + np.exp(-2. * grid_squared))
        integrand_2_no_nan = np.nan_to_num(integrand_2)
        expected_trapz_solution_2 = (2. / np.pi)**(3/2) * np.trapz(y=masked_integrand, x=np.ravel(self.grid))
        assert np.abs(expected_trapz_solution_2 - new_coefficient_2) < 1.


    def test_updating_10_coefficients_using_trapz(self):
        initial_coefficients = np.array([1., 2., 100., 25., 10000., 150., 1230. ,15., 120., 125.])
        EXPONENTS = np.array([2., 5., 3., 1., 0.05, 0.01, 12, 2.5, 1.2, 10000.])

        coefficients_MBIS = update_coefficients(initial_coefficients, EXPONENTS, self.electron_density, self.grid)

        integrand = np.ravel(self.electron_density).copy()
        denominator = 0
        for x in range(0, len(initial_coefficients)):
            denominator += initial_coefficients[x] * np.exp(-EXPONENTS[x] * np.ravel(self.grid)**2)
        integrand /= denominator

        for x in range(0, len(initial_coefficients)):
            expected_answ = np.trapz(y=integrand * np.exp(-EXPONENTS[x] * np.ravel(self.grid)**2) *\
                                     initial_coefficients[x] * (EXPONENTS[x] / np.pi)**(3/2), x=np.ravel(self.grid))
            assert np.abs(expected_answ - coefficients_MBIS[x]) < 1e-10




class Test_Iterative_MBIS_Method(Default_Setup_For_MBIS):
    def check_iterative_updating_one_coefficients(self, coefficient, exponent, error_threshold):
        """
        Note: Since this is a single gaussian function
        The new coefficient should not change after
        one iteration
        """
        coefficient_1, error = iterative_MBIS_method(coefficient, exponent, self.electron_density, self.grid,
                                              error=1e-5)
        expected_trapz_solution = 2 * (exponent[0] / np.pi)**(1/2) *\
                                        np.trapz(y=np.ravel(self.electron_density)[0:219], x=np.ravel(self.grid)[0:219])
        assert error == 0.
        print("Absolute difference=", np.abs(expected_trapz_solution - coefficient_1[0]), expected_trapz_solution, coefficient_1)
        assert np.abs(expected_trapz_solution - coefficient_1[0]) < error_threshold

        return np.abs(expected_trapz_solution - coefficient_1[0])

    def test_iterative_updating_one_coefficient_very_small_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([0.05])
        self.check_iterative_updating_one_coefficients(coeff, exponent, 1e-15)

    def test_iterative_updating_one_coefficient_small_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([5.])
        self.check_iterative_updating_one_coefficients(coeff, exponent, 1e-5)

    def test_iterative_updating_one_coefficient_small_medium_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([25.])
        self.check_iterative_updating_one_coefficients(coeff, exponent, 1e-1)

    def test_iterative_updating_one_coefficient_medium_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([50.])
        self.check_iterative_updating_one_coefficients(coeff, exponent, error_threshold=1.)

    def test_iterative_updating_one_coefficient_large_medium_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([100.])
        self.check_iterative_updating_one_coefficients(coeff, exponent, error_threshold=12)

    def test_iterative_updating_one_coefficient_very_large_exponent(self):
        coeff = np.array([5.])
        exponent = np.array([1000.])
        self.check_iterative_updating_one_coefficients(coeff, exponent, error_threshold=3200)

    def check_plot_different_exponents(self, coefficient_value):
        constant_coefficient = np.array([coefficient_value])
        list_of_exponents = np.arange(0.01, 1000., 50.3)
        list_of_errors = []
        for exp in list_of_exponents:
            error = self.check_iterative_updating_one_coefficients(constant_coefficient,
                                                                   np.array([exp]), 1e20)
            list_of_errors.append(error)
        import matplotlib.pyplot as plt
        plt.title("MBIS Fitting Method of Coeff for One Gaussian Function With Fixed Coeff of " + str(coefficient_value))
        plt.plot(list_of_exponents, list_of_errors)
        plt.xlabel("The Exponent Used As An Initial Guess")
        plt.ylabel("|Difference Between MBIS Solution and Trapz Solution (Coeff)|")
        plt.savefig("2016-07-12_MBIS_Fitting_Error_Coeffs")
        plt.show()

    def check_plot_different_coeffs(self, exponent_value):
        constant_exponents = np.array([exponent_value])
        list_of_coefficients = np.arange(0.01, 1000., 15.3)
        list_of_errors = []
        for coeff in list_of_coefficients:
            error = self.check_iterative_updating_one_coefficients(np.array([coeff]),
                                                                   constant_exponents, 1e20)
            list_of_errors.append(error)
        print(list_of_errors)
        import matplotlib.pyplot as plt
        plt.title("MBIS Fitting Method of Coeff for One Gaussian Function With Fixed Exp of " + str(exponent_value))
        plt.plot(list_of_coefficients,list_of_errors, 'b')
        plt.xlabel("The Coeff Used As An Initial Guess")
        plt.ylabel("|Difference Between MBIS Solution and Trapz Solution (Coeff)|")
        plt.savefig("2016-07-12_MBIS_Fitting_Error_Exps")
        plt.show()

    def test_plot_number_of_zeros_in_integrand(self):
        constant_coefficient = np.array([5.])
        list_of_exponents = np.arange(0.01, 10000., 25.3)
        list_of_number_of_zeroes = []

        for exp in list_of_exponents:
            gaussian_density = np.dot(np.array([exp]), constant_coefficient)

            masked_gaussian_density = np.ma.asarray(gaussian_density)
            masked_electron_density = np.ma.asarray(np.ravel(self.electron_density))

            integrand = masked_electron_density * np.ravel(np.ma.asarray(np.exp(- exp * np.power(self.grid, 2.))))\
                / masked_gaussian_density
            list_of_number_of_zeroes.append(len(integrand[integrand == 0.]))
        print(list_of_number_of_zeroes)
        import matplotlib.pyplot as plt
        plt.title("How many zeroes Are In the Integrand Based on the Exponent Using Masked Aray")
        plt.plot(list_of_number_of_zeroes, list_of_exponents)
        plt.ylabel("Number of Zeroes in the Integrand")
        plt.xlabel("The Exponent Used As An Initial Guess")
        plt.savefig("2016-07-12_MBIS_Fitting_Zeroes")
        plt.show()

    def test_plot_of_integrand(self):
        constant_coefficient = np.array([5.])
        list_of_exponents = np.arange(0.01, 1000., 50.3)
        list_of_number_of_zeroes = []

        for exp in list_of_exponents:
            gaussian_density = np.dot(np.array([exp]), constant_coefficient)

            masked_gaussian_density = np.ma.asarray(gaussian_density)
            masked_electron_density = np.ma.asarray(np.ravel(self.electron_density))

            integrand = masked_electron_density * np.ravel(np.ma.asarray(np.exp(- exp * np.power(self.grid, 2.))))\
                / masked_gaussian_density
            import matplotlib.pyplot as plt
            plt.plot(np.ravel(self.grid)[0:50], integrand[0:50])
        plt.show()

    def test(self):
        self.check_plot_different_coeffs(0.05)
        self.check_plot_different_exponents(5.)

    def chec(self):
        initial_coefficients = np.array([5.0])
        constant_exponents = np.array([20.])
        current_error = 1e5
        while current_error < 1e-5:
            initial_coefficients = (constant_exponents[0] / np.pi)**(3/2) *\
                                        np.trapz(y=np.ravel(self.electron_density), x=np.ravel(self.grid))

            current_error = measure_error_by_integration_of_difference()

    def test2(self):
        initial_coefficients = np.array([1. for x in range(0, 25)])
        exponents = self.be.UGBS_s_exponents#np.array([np.random.random() for x in range(0, 25)])
        #exponents[0:25] = 1.
        new_coeffs, error = iterative_MBIS_method(initial_coefficients, exponents, self.electron_density, self.grid)
        model = self.be.create_model(np.append(new_coeffs, exponents), 25)
        error = self.be.integrate_model_using_trapz(model)
        print(error)



if __name__ == "__main__":
    unittest.main()

