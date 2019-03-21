import inspect

from shared_workflow import shared
from testing.test_common_set_up import (
    INPUT,
    OUTPUT,
    set_up,
    get_input_params,
    get_bench_output,
)


# test for install_simualtion inside install_cybershake_fault.py
def test_get_stations(set_up):
    func_name = "get_stations"
    params = inspect.getfullargspec(shared.get_stations).args
    for root_path, _ in set_up:
        input_params = get_input_params(root_path, func_name, params)
        test_output = shared.get_stations(*input_params)
        bench_output = get_bench_output(root_path, func_name)
        assert test_output == bench_output


def test_user_select(set_up, mocker):
    func_name = "user_select"
    params = inspect.getfullargspec(shared.user_select).args
    for root_path, realisation in set_up:
        input_params = get_input_params(root_path, func_name, params)
        mocker.patch('shared_workflow.shared.input', lambda x: "2")
        test_output = shared.user_select(*input_params)
        bench_output = get_bench_output(root_path, func_name)
        assert test_output == bench_output


def test_get_partition():
    assert shared.get_partition("maui") == "nesi_research"
    assert shared.get_partition("mahuika") == "large"


def test_convert_time_to_hours():
    assert shared.convert_time_to_hours("00:10:00") == 10 / 60.0
    assert shared.convert_time_to_hours("01:00:00") == 1
