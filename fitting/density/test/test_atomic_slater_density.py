import math
import os
from fitting.density.slater_density.atomic_slater_density import *


# TODO ADD TESTS FOR CORE
# TODO ADD TESTS FOR VALENCE
def slater_function(exponent, n, r):
    """Calculates the normalized slater function at a given point.

    ** Arguments **

        exponent    a float or int representing the exponent of the slater function
        n           a float or int representing the natural number
        r           a float or int representing the distance of the electron from the nucleus.
    """
    assert isinstance(exponent, int) or isinstance(exponent, float)
    assert isinstance(n, int) or isinstance(n, float)
    assert isinstance(r, int) or isinstance(r, float)
    normalization = np.power(2. * exponent, n) * math.sqrt(2. * exponent / math.factorial(2*n))
    slater_orbital = np.power(r, n-1) * math.exp(-exponent * r)
    return normalization * slater_orbital


def test_slater_type_orbital_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using one grid point at 1.0
    be = Atomic_Density(file_path, np.array([[1]]))
    calculated = be.slator_type_orbital(np.array([[12.683501]]), np.array([[1]]), np.array([[1]]))
    expected = (2. * 12.683501)**1 * math.sqrt((2 * 12.683501) /
                                               math.factorial(2 * 1)) * 1**0 * math.exp(-12.683501 * 1)
    assert abs(calculated - expected) < 1.e-6
    calculated = be.slator_type_orbital(np.array([[0.821620]]), np.array([[2]]), np.array([[2]]))
    expected = (2. * 0.821620)**2 * math.sqrt((2 * 0.821620) /
                                              math.factorial(2 * 2)) * 2**1 * math.exp(-0.821620 * 2)
    assert abs(calculated - expected) < 1.e-6
    # using two grid points at 1.0 and 2.0
    exp__array = np.array([[12.683501], [0.821620]])
    quantum__array = np.array([[1], [2]])
    grid = np.array([[1], [2]])
    # rows are the slator_Type orbital, where each column represents each point in the grid
    calculated = be.slator_type_orbital(exp__array, quantum__array, grid)
    expected1 = [(2 * 12.683501)**1 * math.sqrt((2 * 12.683501) / math.factorial(2 * 1)) * 1**0 *
                 math.exp(-12.683501 * 1),
                 (2 * 12.683501)**1 * math.sqrt((2 * 12.683501) / math.factorial(2 * 1)) * 2**0 *
                 math.exp(-12.683501 * 2)]
    expected2 = [(2 * 0.821620)**2 * math.sqrt((2 * 0.821620) / math.factorial(2 * 2)) * (1**1) *
                 math.exp(-0.821620 * 1),
                 (2 * 0.821620)**2 * math.sqrt((2 * 0.821620) / math.factorial(2 * 2)) * (2**1) *
                 math.exp(-0.821620 * 2)]
    # every row corresponds to one exponent evaluated on all grid points
    expected = np.array([expected1, expected2])
    assert (abs(calculated - expected) < 1.e-6).all()


def test_slater_dict_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using one grid point at 1.0
    be = Atomic_Density(file_path, np.array([[1]]))
    be_orbitals = be.slator_dict()
    assert be_orbitals.keys() == ['S']
    assert be_orbitals['S'].shape == (1, 8)
    expected = (2 * 12.683501)**1 * math.sqrt((2 * 12.683501) / math.factorial(2 * 1)) * 1**0 * math.exp(-12.683501 * 1)
    assert (abs(be_orbitals['S'][(0, 0)] - expected) < 1.e-6).all()


def test_slater_dict_Be_2():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using two grid points at 1.0 and 2.0
    be = Atomic_Density(file_path, np.array([[1], [2]]))
    be_orbitals = be.slator_dict()
    assert be_orbitals.keys() == ['S']
    assert be_orbitals['S'].shape == (2, 8)
    expected = (2 * 12.683501)**1 * math.sqrt((2 * 12.683501)/ math.factorial(2 * 1)) * 1**0 * math.exp(-12.683501 * 1)
    assert (abs(be_orbitals['S'][(0, 0)] - expected) < 1.e-6).all()
    expected = (2 * 1.406429)**1 * math.sqrt((2 * 1.406429)/ math.factorial(2 * 1)) * 2**0 * math.exp(-1.406429 * 2)
    assert (abs(be_orbitals['S'][(1, 5)] - expected) < 1.e-6).all()


def test_all_coeff_matrix_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using one grid point at 1.0
    be = Atomic_Density(file_path, np.array([[1]]))
    coeff_s = be.all_coeff_matrix('S')
    assert coeff_s.shape == (8, 2)
    coeff_1s = np.array([-0.0024917, 0.0314015, 0.0849694, 0.8685562, 0.0315855, -0.0035284, -0.0004149, .0012299])
    coeff_2s = np.array([0.0004442, -0.0030990, -0.0367056, 0.0138910, -0.3598016, -0.2563459, 0.2434108, 1.1150995])
    expected = np.hstack((coeff_1s.reshape(8, 1), coeff_2s.reshape(8, 1)))
    assert (abs(coeff_s - expected) < 1.e-6).all()


def test_phi_LCAO_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using one grid point at 1.0
    be = Atomic_Density(file_path, np.array([[1]]))
    phi = be.phi_LCAO('S')
    assert phi.shape == (1, 2)
    r = 1
    LCAO1S = slater_function(12.683501, 1, r)*-0.0024917 + slater_function(8.105927, 1, r)*0.0314015
    LCAO1S += slater_function(5.152556, 1, r)*0.0849694 + slater_function(3.472467, 1, r)*0.8685562
    LCAO1S += slater_function(2.349757, 1, r)*0.0315855 + slater_function(1.406429, 1, r)*-0.0035284
    LCAO1S += slater_function(0.821620, 2, r)*-0.0004149 + slater_function(0.786473, 1, r)*0.0012299

    LCAO2S = slater_function(12.683501, 1, r)*0.0004442 + slater_function(8.105927, 1, r)*-0.0030990
    LCAO2S += slater_function(5.152556, 1, r)*-0.0367056 + slater_function(3.472467, 1, r)*0.0138910
    LCAO2S += slater_function(2.349757, 1, r)*-0.3598016 + slater_function(1.406429, 1, r)*-0.2563459
    LCAO2S += slater_function(0.821620, 2, r)*0.2434108 + slater_function(0.786473, 1, r)*1.1150995
    assert abs(phi[(0, 0)] - LCAO1S) < 1.e-6
    assert abs(phi[(0, 1)] - LCAO2S) < 1.e-6


def test_phi_LCAO_Be_2():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using three grid points at 1.0, 2.0, and 3.0
    be = Atomic_Density(file_path, np.array([[1], [2], [3]]))
    phi = be.phi_LCAO('S')
    assert phi.shape == (3, 2)
    # expected values are taken from the previous example
    assert abs(phi[(0, 0)] - 0.38031668) < 1.e-6
    assert abs(phi[(0, 1)] - 0.3278693) < 1.e-6


def test_phi_matrix_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # using one grid point at 1.0
    be = Atomic_Density(file_path, np.array([[1]]))
    # check the values of the phi_matrix
    phi_matrix = be.phi_matrix()
    assert phi_matrix.shape == (1, 2)
    r = 1.0
    phi1S = slater_function(12.683501, 1, r) * -0.0024917 + slater_function(8.105927, 1, r) * 0.0314015
    phi1S += slater_function(5.152556, 1, r) * 0.0849694 + slater_function(3.472467, 1, r) * 0.8685562
    phi1S += slater_function(2.349757, 1, r) * 0.0315855 + slater_function(1.406429, 1, r) * -0.0035284
    phi1S += slater_function(0.821620, 2, r) * -0.0004149 + slater_function(0.786473, 1, r) * 0.00122991

    phi2S = slater_function(12.683501, 1, r) * 0.0004442 + slater_function(8.105927, 1, r) * -0.0030990
    phi2S += slater_function(5.152556, 1, r) * -0.0367056 + slater_function(3.472467, 1, r) * 0.0138910
    phi2S += slater_function(2.349757, 1, r) * -0.3598016 + slater_function(1.406429, 1, r) * -0.2563459
    phi2S += slater_function(0.821620, 2, r) * 0.2434108 + slater_function(0.786473, 1, r) * 1.1150995
    expected = np.concatenate((np.array([phi1S]), np.array([phi2S])))
    assert (abs(phi_matrix - expected) < 1.e-6).all()


def test_phi_LCAO_Be_integrate():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # placing 100,000 equally distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    be = Atomic_Density(file_path, grid.reshape(len(grid), 1))
    phi = be.phi_LCAO('S')
    assert phi.shape == (len(grid), 2)
    # check: integrating the density of each orbital should result in one
    dens_1s = np.power(phi[:, 0], 2)
    dens_2s = np.power(phi[:, 1], 2)
    assert dens_1s.shape == dens_2s.shape == grid.shape
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    integrate_1s = np.trapz((grid**2) * dens_1s, grid)
    integrate_2s = np.trapz((grid**2) * dens_2s, grid)
    assert abs(integrate_1s - 1.0) < 1.e-4
    assert abs(integrate_2s - 1.0) < 1.e-4
    # integrate(r^2 * density(r)) using the composite Simpsons rule.
    import scipy
    integrate_1s = scipy.integrate.simps((grid**2) * dens_1s, grid)
    integrate_2s = scipy.integrate.simps((grid**2) * dens_2s, grid)
    assert abs(integrate_1s - 1.0) < 1.e-4
    assert abs(integrate_2s - 1.0) < 1.e-4


def test_phi_LCAO_Ne_integrate():
    # load the Ne file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/ne.slater'
    # placing 100,000 eqully distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    ne = Atomic_Density(file_path, grid.reshape(len(grid), 1))
    phi_s = ne.phi_LCAO('S')
    phi_p = ne.phi_LCAO('P')
    assert phi_s.shape == (len(grid), 2)
    assert phi_p.shape == (len(grid), 1)
    # check: integrating the density of each orbital should result in one
    dens_1s = np.power(phi_s[:, 0], 2)
    dens_2s = np.power(phi_s[:, 1], 2)
    dens_2p = np.power(np.ravel(phi_p), 2)
    assert dens_1s.shape == dens_2s.shape == grid.shape
    assert dens_2p.shape == grid.shape
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    assert abs(np.trapz(np.power(grid, 2) * dens_1s, grid) - 1.0) < 1.e-6
    assert abs(np.trapz(np.power(grid, 2) * dens_2s, grid) - 1.0) < 1.e-6
    assert abs(np.trapz(np.power(grid, 2) * dens_2p, grid) - 1.0) < 1.e-6


def test_phi_LCAO_C_integrate():
    # load the C file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/c.slater'
    # placing 100,000 eqully distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    c = Atomic_Density(file_path, grid)
    phi_s = c.phi_LCAO('S')
    phi_p = c.phi_LCAO('P')
    assert phi_s.shape == (len(grid), 2)
    assert phi_p.shape == (len(grid), 1)
    # check: integrating the density of each orbital should result in one
    dens_1s = np.power(phi_s[:, 0], 2)
    dens_2s = np.power(phi_s[:, 1], 2)
    dens_2p = np.power(np.ravel(phi_p), 2)
    assert dens_1s.shape == dens_2s.shape == grid.shape
    assert dens_2p.shape == grid.shape
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    assert abs(np.trapz(np.power(grid, 2) * dens_1s, grid) - 1.0) < 1.e-5
    assert abs(np.trapz(np.power(grid, 2) * dens_2s, grid) - 1.0) < 1.e-5
    assert abs(np.trapz(np.power(grid, 2) * dens_2p, grid) - 1.0) < 1.e-5


def test_atomic_density_Be():
    # load the Be file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/be.slater'
    # placing 100,000 eqully distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    be = Atomic_Density(file_path, grid.reshape(len(grid), 1))
    # get the density and flatten the array
    density = np.ravel(be.atomic_density())
    assert density.shape == grid.shape
    # check: integrating atomic density should result in the number of electrons.
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    assert abs(np.trapz(np.power(grid, 2) * density, grid) * 4. * np.pi - 4.0) < 1.e-3


def test_atomic_density_Ne():
    # load the Ne file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/ne.slater'
    # placing 100,000 eqully distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    ne = Atomic_Density(file_path, grid.reshape(len(grid), 1))
    # get the density and flatten the array
    density = np.ravel(ne.atomic_density())
    assert density.shape == grid.shape
    # check: integrating atomic density should result in the number of electrons.
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    assert abs(np.trapz(np.power(grid, 2) * density, grid) * 4. * np.pi - 10.0) < 1.e-6


def test_atomic_density_C():
    # load the C file
    file_path = os.path.dirname(__file__).rsplit('/', 2)[0] + '/data/examples/c.slater'
    # placing 100,000 eqully distant points from 0.0 to 10.0 for accurate integration
    grid = np.arange(0.0, 10.0, 0.0001)
    c = Atomic_Density(file_path, grid.reshape(len(grid), 1))
    # get the density and flatten the array
    density = np.ravel(c.atomic_density())
    assert density.shape == grid.shape
    # check: integrating atomic density should result in the number of electrons.
    # integrate(r^2 * density(r)) using the composite trapezoidal rule.
    assert abs(np.trapz(np.power(grid, 2) * density, grid) * 4. * np.pi - 6.0) < 1.e-5

if __name__ == "__main__":
    test_phi_LCAO_C_integrate()
    test_atomic_density_Ne()
    test_atomic_density_Be()
    test_phi_LCAO_Be_integrate()
    test_phi_matrix_Be()
    test_phi_LCAO_Be_2()
    test_phi_LCAO_Be()
    test_all_coeff_matrix_Be()
    test_slater_dict_Be()
    test_slater_type_orbital_Be()
    test_atomic_density_C()
