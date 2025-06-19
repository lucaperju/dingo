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
from scipy.linalg import eigh

def evaluate_rounding_quality(A, b, method='billiard_walk', n_samples=None, seed=42):
    d = A.shape[1]
    if n_samples is None:
        n_samples = 10 * d

    burn_in = int(5 * np.sqrt(d))
    thinning = burn_in

    print("starting sampling")
    samples = PolytopeSampler.sample_from_polytope_no_multiphase(
        A, b,
        method=method,
        n=n_samples,
        burn_in=burn_in,
        thinning=thinning
    )

    print("done sampling")

    samples = samples.T

    X = samples
    X_centered = X - X.mean(axis=0)
    cov = np.cov(X_centered, rowvar=False)

    I = np.eye(d)
    diff = cov - I
    frob_err = np.linalg.norm(diff, 'fro')
    spec_err = np.linalg.norm(diff, 2)
    eigvals = eigh(cov, eigvals_only=True)
    scale = eigvals.mean()

    return {
        "frobenius_error": frob_err,
        "spectral_error": spec_err,
        "scaling_factor": scale,
        "eigenvalues": eigvals,
        "covariance": cov
    }


def test_rounding(rounding_method, transformed_polytope, name):
    if rounding_method == "PolyRound":
        start = time.time()
        rounded_polytope = PolyRoundApi.round_polytope(transformed_polytope)
        end   = time.time()
        A = rounded_polytope.A.to_numpy()
        b = rounded_polytope.b.to_numpy()
        #result = evaluate_rounding_quality(A, b)
        P = HPolytope(A, b)
        min_axis, max_axis, ratio = P.assess_rounding()
        print("Polytope derived from the " + name + " network, took " + str(end - start) + " sec to get rounded with PolyRound. With ratio " + str(ratio));
        #print("Scaling estimate (should be ~1):", result['scaling_factor'])
        #print("Frobenius norm error:", result['frobenius_error'])
        #print("Spectral norm error:", result['spectral_error'])
        print("\n\n")
    else:
        A = transformed_polytope.A.to_numpy()
        b = transformed_polytope.b.to_numpy()
        P = HPolytope(A, b)
        start = time.time()
        A_rounded, b_rounded, x, y, z = P.rounding(rounding_method, None)
        end   = time.time()
        #result = evaluate_rounding_quality(A_rounded, b_rounded)
        P = HPolytope(A_rounded, b_rounded)
        min_axis, max_axis, ratio = P.assess_rounding()
        print("Polytope derived from the " + name + " network, took " + str(end - start) + " sec to get rounded with " + rounding_method + ". With ratio " + str(ratio));
        #print("Scaling estimate (should be ~1):", result['scaling_factor'])
        #print("Frobenius norm error:", result['frobenius_error'])
        #print("Spectral norm error:", result['spectral_error'])
        print("\n\n")

def polyround_preprocess(model_path):

    print("Starting PolyRound preprocessing for " + model_path)

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

    test_rounding("PolyRound", transformed_polytope, name)
    test_rounding("isotropic_position", transformed_polytope, name)
    test_rounding("min_ellipsoid", transformed_polytope, name)
    test_rounding("john_position", transformed_polytope, name)
    test_rounding("log_barrier", transformed_polytope, name)
    test_rounding("volumetric_barrier", transformed_polytope, name)
    test_rounding("vaidya_barrier", transformed_polytope, name)

    
    # Export rounded polytope as pickle file
    #polytope_info = (
    #    rounded_polytope,
    #    name,
    #)

    #with open(
    #    "polyrounded_polytopes/polytope_" + name + ".pckl", "wb"
    #) as polyround_polytope_file:
    #    pickle.dump(polytope_info, polyround_polytope_file)

    # return rounded_polytope, name
    return


if __name__ == '__main__':

    set_default_solver("gurobi")
    current_directory = os.getcwd()
    network_name = sys.argv[1]
    dingo_directory = '/'.join(current_directory.split("/")[:-1])

    path_to_net = dingo_directory + "/ext_data/" + network_name
    print(path_to_net)
    # rpolytope, name = polyround_preprocess(path_to_net)
    polyround_preprocess(path_to_net)
