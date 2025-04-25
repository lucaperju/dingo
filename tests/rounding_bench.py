#!/usr/bin/python3

import os, sys, time, getopt
import numpy as np
import pickle
from PolyRound.api import PolyRoundApi
from PolyRound.static_classes.lp_utils import ChebyshevFinder
from PolyRound.settings import PolyRoundSettings
import hopsy
import dingo
from dingo import MetabolicNetwork, PolytopeSampler

from dingo import set_default_solver
from volestipy import HPolytope
import gurobipy

def polyround_preprocess(model_path):

    name = model_path.split("/")[-1]

    # Import model and create Polytope object
    polytope = PolyRoundApi.sbml_to_polytope(model_path)
    print("Polyope for network " + name + " was built.")

    # Make a settings object for the polyround library - optional
    settings = PolyRoundSettings()

    # Simplify the polytope
    start = time.time()
    simplified_polytope = PolyRoundApi.simplify_polytope(polytope)
    end   = time.time()
    time_for_simplification = end - start
    print("Polytope derived from the " + name + " network, took " + str(time_for_simplification) + " sec to get simplified.")

    # Polytope transformation
    start = time.time()
    transformed_polytope = PolyRoundApi.transform_polytope(simplified_polytope)
    end   = time.time()
    time_for_transformation = end - start
    print("Polytope derived from the " + name + " network, took " + str(time_for_transformation) + " sec to get transformed.")

    # Export simplified and transformed polytope as pickle file
    polytope_info = (
        transformed_polytope,
        name,
    )

    with open(
        "simpl_transf_polytopes/polytope_" + name + ".pckl", "wb"
    ) as polyround_polytope_file:
        pickle.dump(polytope_info, polyround_polytope_file)

    # Rounding
    start = time.time()
    rounded_polytope = PolyRoundApi.round_polytope(transformed_polytope)
    end   = time.time()
    time_for_rounding = end - start
    print("Polytope derived from the " + name + " network, took " + str(time_for_rounding) + " sec to get rounded.")

    # roudning with dingo
    A = transformed_polytope.A.to_numpy()
    b = transformed_polytope.b.to_numpy()
    P = HPolytope(A, b)

    #start = time.time()
    #P.rounding("isotropic_position", None)
    #end   = time.time()
    #print("Polytope derived from the " + name + " network, took " + str(end - start) + " sec to get rounded (dingo).")

    #start = time.time()
    #P.rounding("min_ellipsoid", None)
    #end   = time.time()
    #print("Polytope derived from the " + name + " network, took " + str(end - start) + " sec to get rounded (dingo).")

    start = time.time()
    P.rounding("john_position", None)
    end   = time.time()
    print("Polytope derived from the " + name + " network, took " + str(end - start) + " sec to get rounded (dingo).")

    # Export rounded polytope as pickle file
    polytope_info = (
        rounded_polytope,
        name,
    )

    with open(
        "polyrounded_polytopes/polytope_" + name + ".pckl", "wb"
    ) as polyround_polytope_file:
        pickle.dump(polytope_info, polyround_polytope_file)

    return rounded_polytope, name


if __name__ == '__main__':

    set_default_solver("gurobi")
    current_directory = os.getcwd()
    network_name = sys.argv[1]
    dingo_directory = '/'.join(current_directory.split("/")[:-1])

    path_to_net = dingo_directory + "/ext_data/" + network_name
    print(path_to_net)
    rpolytope, name = polyround_preprocess(path_to_net)
