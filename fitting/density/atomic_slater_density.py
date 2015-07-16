
import sys
import numpy as np
import scipy.misc
import scipy
import scipy.integrate
import matplotlib.pyplot as plt
import sympy as sp

from fitting.density.atomic_slater_wfn import *


class Atomic_Density():
    """
    Insert Documentations
    """
    def __init__(self, file_name, grid):
        self.VALUES = load_slater_wfn(file_name)
        self.GRID = grid
        self.ALL_SLATOR_ORBITALS = self.slator_dict()

    def slator_type_orbital(self, exponent, quantumNum, r):
        """
        Computes the Slator Type Orbital equation.

        :param exponent: alpha
        :param quantumNum: principal quantum number
        :param r: distance form the nuclei
        :return: returns a number or an array depending on input values
        """
        assert exponent.shape == quantumNum.shape
        assert exponent.shape[1] == 1
        assert quantumNum.shape[1] == 1
        #assert r.shape[1] == 1

        normalization = ((2 * exponent)**quantumNum) * np.sqrt(((2 * exponent) / scipy.misc.factorial(2 * quantumNum)))
        assert normalization.shape == exponent.shape
        pre_factor = np.transpose(r ** (np.ravel(quantumNum) - 1))
        slater =  pre_factor * (np.exp(-exponent * np.transpose(r)))
        slater *= normalization
        return slater

    def slator_dict(self):
        """
        Groups Each Slater Equations Based On The SubShell inside an dictionary.
        This is then used to multiply by coefficient array to obtain all phi equations
        for that subshell. Hence each subshell will have their own slator matrix
        and their own coefficient matrix, dot product between them will obtain
        the phi equations(MO) for that subshell.

        :return: row = number of points, column = number of slater equations
        """
        dict_orbital = {x[1]:0 for x in self.VALUES['orbitals'] }
        for subshell in dict_orbital.keys():
            exponents = self.VALUES['orbitals_exp'][subshell]
            basis_numbers = self.VALUES['basis_numbers'][subshell]
            slater = self.slator_type_orbital(exponents, basis_numbers, self.GRID)
            dict_orbital[subshell] = np.transpose(slater)
        return dict_orbital

    def all_coeff_matrix(self, subshell):
        """
        This Groups all of the coefficients based on the subshell.
        This is then used to multiply by the specific slator array from the
        slator_dict function, in order to obtain a phi array.

        :param subshell: this is either S or P or D Or F
        :return: an array where row = number of coefficients per orbital and column = number of orbitals of
                    specified subshell.
        """

        #This obtains the coefficients of the specified subshell in the form of an dictionary where values = np.array
        subshell_coeffs = {key:VALUES for key, VALUES in self.VALUES['orbitals_coeff'].items() if subshell == key[1]}

        counter = 0;
        array_coeffs = None

        for key in [x for x in self.VALUES['orbitals'] if x[1] == subshell]:
            if counter == 0:    #initilize the array
                array_coeffs = self.VALUES['orbitals_coeff'][key]
                counter += 1;
            else:
                array_coeffs = np.concatenate((array_coeffs, self.VALUES['orbitals_coeff'][key]), axis = 1)

        return array_coeffs

    def phi_LCAO(self, subshell):
        """
        Calculates phi/linear combination of atomic orbitals
        by the dot product of slator array (from slator_dict)
        and coeff array (from all_coeff_matrix(subshell)) for
        a specific subshell. Hence, to obtain all of the
        phi equations for the specific element it must be
        repeated for each subshell (S & P & D & F).

        :return: array where row = number of points and column = number of phi/orbitals.
                For example, beryllium will have row = # of points and column = 2 (1S and 2S)
        """
        return np.dot(self.ALL_SLATOR_ORBITALS[subshell], self.all_coeff_matrix(subshell))

    def phi_matrix(self): #connect all phis together
        """
        Connects phi equations into an array, horizontally.
        For Example, for beryllium [phi(1S), phi(2S)] is the array.
        E.G. Carbon [phi(1S), phi(2S), phi(2P)].
        :return: array where all of the phi equations
                 for each orbital is connected together, horizontally.
                 row = number of points and col = each phi equation for each orbital
        """
        list_orbitals = ['S', 'P', 'D', 'F']

        counter = 0
        phi_matrix = 0
        for orbital in list_orbitals:
            if orbital in self.VALUES['orbitals_exp'].keys():
                if counter == 0:        #initilize array
                    phi_matrix = self.phi_LCAO(orbital)
                    counter += 1
                else:
                    phi_matrix = np.concatenate((phi_matrix, self.phi_LCAO(orbital)), axis = 1)
        return phi_matrix

    def atomic_density(self):
        """
        By Taking the occupation numbers and multiplying it
        by the corresponding absolute, squared phi to obtain
        electron density(rho).

        :return: the electron density where row = number of point
                 and column = 1
        """
        return np.dot(np.absolute(self.phi_matrix())**2, self.VALUES['orbitals_electron_array'] )

    def atomic_density_core(self):
        """
        Calculates Atomic Density for
        core and valence electrons.
        :return:
        """

        def energy_homo():
            """
            A helper function that finds the HOMO energy of
            the element
            :return: Energy Of Homo
            """
            #initilize the energy from first value from the list
            energy_homo = self.VALUES['orbitals_energy']['S'][0]

            for orbital,list_energy in self.VALUES['orbitals_energy'].items():
                max_of_list = np.max(list_energy)
                if max_of_list > energy_homo:
                    energy_homo = max_of_list
            return(energy_homo)

        energy_homo = energy_homo()
        print(energy_homo)
        print(self.VALUES['orbitals_energy'])

        def join_energy():
            """
            A helper function to join all of the energy
            levels into one array
            :return:
            """
            joined_array = np.array([])
            for orbital in ['S', 'P', 'D', 'F']:
                if orbital in self.VALUES['orbitals_energy']:
                    orbital_energy = self.VALUES['orbitals_energy'][orbital]
                    joined_array = np.hstack([joined_array, orbital_energy])
            return joined_array


        phi_matrix = self.phi_matrix()
        energy_difference = join_energy() - energy_homo

        absolute_squared = 1 -   np.exp((-1) * np.absolute((energy_difference)**2))
        core = absolute_squared * np.absolute(phi_matrix)**2

        absolute_squared_val = np.exp((-1) * np.absolute((energy_difference)**2))
        valence = absolute_squared_val * np.absolute(phi_matrix)**2


        return(np.dot(core, self.VALUES['orbitals_electron_array'] ),\
               np.dot(valence, self.VALUES['orbitals_electron_array']))

r"""
p, w = np.polynomial.laguerre.laggauss(185)
p = np.reshape(p, (len(p), 1))
w = np.reshape(w, (len(w), 1))
be = Atomic_Density(r'C:\Users\Alireza\PycharmProjects\fitting\fitting\data\examples\be.slater', p)

hey = be.atomic_density_core()

a = hey[0] * p**2 * w/ np.exp(-p)
b = hey[1] * p**2 * w/np.exp(-p)

print(np.sum(a), np.sum(b))
"""


