import os
import pytest
import pickle

from qcore import testing

INPUT = "input"
OUTPUT = "output"
REALISATIONS = [
    (
        "PangopangoF29_HYP01-10_S1244",
        "http://ec2-13-211-174-16.ap-southeast-2.compute.amazonaws.com:5000//static/public/testing/slurm_gm_workflow/PangopangoF29_HYP01-10_S1244.zip",
    )
]


def get_fault_from_rel(realisation):
    return realisation.split("_")[0]


def get_input_params(root_path, func_name, params):
    input_params = []
    for param in params:
        with open(
            os.path.join(root_path, INPUT, func_name + "_{}.P".format(param)), "rb"
        ) as load_file:
            input_param = pickle.load(load_file)
            input_params.append(input_param)
    return input_params


def get_bench_output(root_path, func_name):
    with open(
        os.path.join(root_path, OUTPUT, func_name + "_ret_val.P"), "rb"
    ) as load_file:
        bench_output = pickle.load(load_file)
    return bench_output


@pytest.yield_fixture(scope="session", autouse=True)
def set_up(request):
    data_locations = testing.test_set_up(REALISATIONS)
    yield list(zip(data_locations, [rel[0] for rel in REALISATIONS]))
    testing.test_tear_down(data_locations)
