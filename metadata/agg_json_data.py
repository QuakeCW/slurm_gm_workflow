#!/usr/bin/env python3
"""Reads metadata json files created by write_json script and combines
the data into a single dataframe, which is then saved as a .csv

Searches recursively for the .json files for a given start dir.

Note: This only works in python3, python2.7 glob does not support
recursive directory traversal.
"""
import ast
import sys
import os
import glob
import json
import numpy as np
import pandas as pd

from multiprocessing import Pool
from argparse import ArgumentParser

from estimation.estimate_wct import get_IM_comp_count
from qcore.constants import (
    ProcessType,
    MetadataField,
    Components,
    METADATA_TIMESTAMP_FMT,
)

DATE_COLUMNS = ["end_time", "start_time", "submit_time"]


def get_row(json_file):
    """Gets a row of metadata for the single simulation json log file"""
    with open(json_file) as f:
        data_dict = json.load(f)

    sim_name = data_dict.get(MetadataField.sim_name.value)
    if sim_name is None:
        print("No simulation name found in json file {}, skipping.".format(json_file))
        return None, None

    columns = []
    data = []

    # Iterate over the json and aggregate the data
    for proc_type in data_dict.keys():
        if ProcessType.has_str_value(proc_type):
            for metadata_field in data_dict[proc_type].keys():
                if MetadataField.has_value(metadata_field):

                    # Special handling as dataframes do not like lists
                    if metadata_field == MetadataField.im_comp.value:
                        for comp in data_dict[proc_type][metadata_field]:
                            columns.append((proc_type, comp))
                            data.append(1)
                        continue

                    columns.append((proc_type, metadata_field))
                    data.append(data_dict[proc_type][metadata_field])

    return sim_name, columns, data


def clean_df(df: pd.DataFrame):
    """Cleans column of interests,
    and attempts to convert columns to numeric data type (float)"""
    # Iterate BB, HF, LF
    for proc_type in ProcessType.iterate_str_values():
        if proc_type in df.columns.levels[0].values:
            # All available metadata
            for meta_col in df[proc_type].columns.values:
                # Run time, remove "hour"
                if MetadataField.run_time.value == meta_col:
                    rt_param = MetadataField.run_time.value

                    # Convert column type to float
                    df[proc_type, rt_param] = np.asarray(
                        [
                            (
                                value.split(" ")[0] if type(value) is str else value
                            )  # Handle np.nan values
                            for value in df[proc_type, rt_param].values
                        ],
                        dtype=np.float32,
                    )
                # Convert date strings to date type
                elif meta_col in DATE_COLUMNS:
                    df[proc_type, meta_col] = pd.to_datetime(
                        df[proc_type, meta_col],
                        format=METADATA_TIMESTAMP_FMT,
                        errors="coerce",
                    )
                # Convert components to boolean
                elif Components.has_value(meta_col):
                    df.loc[df[proc_type, meta_col].isna(), (proc_type, meta_col)] = 0.0
                    df[(proc_type, meta_col)] = df[(proc_type, meta_col)].astype(
                        np.bool
                    )
                # Try to convert everything else to numeric
                else:
                    df[proc_type, meta_col] = pd.to_numeric(
                        df[proc_type, meta_col], errors="coerce", downcast="float"
                    )

    return df


def get_IM_comp_count_from_str(str_list: str, real_name: str):
    """Gets the IM component count, see get_IM_comp_count for better doc"""
    try:
        comp = ast.literal_eval(str_list)
    except ValueError:
        print("Failed to determine number of components for {}".format(real_name))
        return np.nan

    return get_IM_comp_count(comp)


def main(args):
    # Check if the output file already exists (No overwrite)
    if os.path.isfile(args.output_file):
        print("Output file already exists. Not proceeding. Exiting.")
        sys.exit()

    # Get all .json files
    print("Searching for matching json files")
    file_pattern = (
        "{}.json".format(args.filename_pattern)
        if args.not_recursive
        else os.path.join("**/", "{}.json".format(args.filename_pattern))
    )

    json_files = [
        glob.glob(os.path.join(cur_dir, file_pattern), recursive=not args.not_recursive)
        for cur_dir in args.input_dirs
    ]

    # Flatten the list of list of files
    json_files = [file for file_list in json_files for file in file_list]

    if len(json_files) == 0:
        print("No matching .json files found. Quitting.")
        sys.exit()
    else:
        print("Found {} matching .json files".format(len(json_files)))

    print(
        "Getting metadat from each simulation using {} number of process".format(
            args.n_procs
        )
    )
    if args.n_procs > 1:
        p = Pool(args.n_procs)
        rows = p.map(get_row, json_files)
    else:
        rows = [get_row(file) for file in json_files]

    print("Creating dataframe...")
    df = None
    for sim_name, columns, data in rows:
        # Create the dataframe
        if df is None:
            df = pd.DataFrame(
                index=[sim_name],
                columns=pd.MultiIndex.from_tuples(columns),
                data=np.asarray(data, dtype=object).reshape(1, -1),
            )
        else:
            # Check/Add missing columns
            column_mask = np.asarray(
                [True if col in df.columns else False for col in columns]
            )
            if np.any(~column_mask):
                for col in columns:
                    if col not in df.columns:
                        df[col] = np.nan

            # Add row data
            df.loc[sim_name, columns] = data

    # Clean the dataframe
    df = clean_df(df)

    # Calculate the core hours for each simulation type
    if args.calc_core_hours:
        for proc_type in ProcessType.iterate_str_values():
            if proc_type in df.columns.levels[0].values:
                cur_df = df.loc[:, proc_type]

                if (
                    MetadataField.run_time.value in cur_df.columns
                    and MetadataField.n_cores.value in cur_df.columns
                ):
                    df.loc[:, (proc_type, MetadataField.core_hours.value)] = (
                        cur_df.loc[:, MetadataField.run_time.value]
                        * cur_df.loc[:, MetadataField.n_cores.value]
                    )
                # Missing run time and number of cores column
                else:
                    print(
                        "Columns {} and {} do no exist for "
                        "simulation type {}".format(
                            MetadataField.run_time.value,
                            MetadataField.run_time.value,
                            proc_type,
                        )
                    )

    print("Saving the final dataframe in {}".format(args.output_file))
    df.to_csv(args.output_file)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input_dirs",
        type=str,
        nargs="+",
        help="Input directory/directories that contains the "
        "json files with the metadata",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="The name of the file to save the " "resulting dataframe",
    )
    parser.add_argument(
        "-n", "--n_procs", type=int, default=4, help="Number of processes to use"
    )
    parser.add_argument(
        "-nr",
        "--not_recursive",
        action="store_true",
        help="Disables recursive file searching",
        default=False,
    )
    parser.add_argument(
        "-fp",
        "--filename_pattern",
        type=str,
        default="metadata_log",
        help="The json file pattern to search. "
        "Do not add .json. Defaults to 'metadata_log'.",
    )
    parser.add_argument(
        "--calc_core_hours",
        action="store_true",
        default=False,
        help="Calculates the total number of core hours "
        "from the run_time and number of cores and adds "
        "them to the dataframe as a column",
    )

    args = parser.parse_args()
    main(args)
