# script to quickly check the status of adv_im for a event
# checks for existance of aggregated csv
# checks for nan/null in the csv
# checks station in csv matches stations ran


import argparse
import pandas as pd

from qcore import constants as const
from qcore.simulation_structure import get_im_calc_dir
from IM_calculation.Advanced_IM.runlibs_2d import check_status

import os
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sim_dir", type=str, help="The path to the realisation directory"
    )
    parser.add_argument(
        "adv_im_model", nargs="+", type=str, help="list of adv_IM models that ran"
    )

    parser.add_argument(
        "--components",
        default=[const.Components.c000.str_value, const.Components.c090.str_value],
        nargs="+",
        choices=list(const.Components.iterate_str_values()),
        help="list of component that ran",
    )

    args = parser.parse_args()

    return args

def check_log(list_folders, model, csv_stations, components):
    """
    check of "Failed" msg in logs
    no "Failed" in all Analysis*.txt == crashed
    "Failed" in all Analysis*.txt == failed to converge (normal)
    """
    for station_dir in list_folders:
        # check if folder is a station run folder
        station_model_dir = os.path.join(station_dir, model)
        station_name = os.path.basename(station_dir)
        if not os.path.isdir(station_model_dir) or (
            station_name in csv_stations
        ):
            # does not match naming for a station run, possibly created by something else, skipping
            continue
        result = True
        for comp in components:
            component_outdir = os.path.join(station_model_dir, comp)
            result = (
                check_status(component_outdir, check_fail=True)
                and result
            )
            # logs shows not all analysis failed to converge, but station failed to create csv
            print(f"{station_dir} failed to run on {model}")
            # break the loop as soon as one component fail the verification
            if not result: return False
    return result
    
def main(sim_dir, adv_im_model, components, exit=True):

    failed = []

    for model in adv_im_model:
        # check if csv exist
        csv_path = os.path.join(sim_dir, "IM_calc/{}.csv".format(model))
        im_dir = get_im_calc_dir(sim_dir)
        # check file exist first to prevent crash
        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            failed.append(model)
            print("csv for {} does not exist".format(model))
            continue
        # check for null/nan
        if df.isnull().values.any():
            failed.append(model)

        # check station count, if match, skip rest of checks
        csv_stations = df.station.unique()
        # glob for station folders
        list_folders = [ y for y in [ os.path.join(im_dir,x) for x in os.listdir(im_dir)] if os.path.isdir(y)]
        if len(csv_stations) == len(list_folders):
            # station folder count matches csv.station.count
            continue
        # check for logs 
        res = check_log(list_folders, model, csv_stations, components)
        if res != True:
            failed.append(model)
    if len(failed) != 0:
        print("some runs have failed. models: {}".format(failed))
        if exit:
            sys.exit(1)
    else:
        print("check passed")
        if exit:
            sys.exit(0)


if __name__ == "__main__":
    args = parse_args()
    main(args.sim_dir, args.adv_im_model, args.components)
