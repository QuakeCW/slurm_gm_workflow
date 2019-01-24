#!/usr/bin/env python3
"""Script to create and submit a slurm script for LF"""
# TODO: import the CONFIG here
# Section for parser to determine if using automate wct
import os
import argparse

import set_runparams
import estimation.estimate_WC as wc

from qcore import utils
from shared_workflow import shared
from shared_workflow.shared_defaults import tools_dir

# TODO: remove this once temp_shared is gone
from temp_shared import resolve_header
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Default values
default_core = 160
default_run_time = "02:00:00"
default_memory = "16G"
default_account = 'nesi00213'
default_ch_scale = 1.1
default_wct_scale = 1.2

params = utils.load_sim_params('sim_params.yaml')


def write_sl_script(
        lf_sim_dir, sim_dir, srf_name, mgmt_db_location, run_time=default_run_time,
        nb_cpus=default_core, memory=default_memory, account=default_account):
    set_runparams.create_run_params(srf_name)
    """Populates the template and writes the resulting slurm script to file"""

    with open('run_emod3d.sl.template', 'r') as f:
        template = f.read()

    replace_t = [("{{lf_sim_dir}}", lf_sim_dir), ("{{tools_dir}}", tools_dir),
                 ("{{mgmt_db_location}}", mgmt_db_location),
                 ("{{sim_dir}}", sim_dir), ("{{srf_name}}", srf_name)]

    for pattern, value in replace_t:
        template = template.replace(pattern, value)

    # slurm header
    job_name = "run_emod3d.%s" % srf_name
    header = resolve_header(
        account, str(nb_cpus), run_time, job_name, "slurm", memory, timestamp,
        job_description="emod3d slurm script",
        additional_lines="#SBATCH --hint=nomultithread")

    fname_slurm_script = 'run_emod3d_%s_%s.sl' % (srf_name, timestamp)
    with open(fname_slurm_script, 'w') as f:
        f.write(header)
        f.write(template)

    fname_sl_abs_path = os.path.join(os.path.abspath(os.path.curdir),
                                     fname_slurm_script)
    print("Slurm script %s written" % fname_sl_abs_path)

    return fname_sl_abs_path


if __name__ == '__main__':
    # Start of main function
    parser = argparse.ArgumentParser(
        description="Create (and submit if specified) the slurm script for LF")

    parser.add_argument("--ncore", type=int, default=default_core)
    parser.add_argument("--auto", nargs="?", type=str, const=True)
    parser.add_argument('--account', type=str, default=default_account)
    parser.add_argument('--srf', type=str, default=None)
    args = parser.parse_args()

    if args.auto:
        submit_yes = True
    else:
        submit_yes = shared.confirm("Also submit the job for you?")

    print("params.srf_file", params.srf_file)
    wall_clock_limit = None
    # Get the srf(rup) name without extensions
    srf_name = os.path.splitext(os.path.basename(params.srf_file))[0]
    if args.srf is None or srf_name == args.srf:
        print("not set_params_only")
        # get lf_sim_dir
        lf_sim_dir = os.path.join(params.sim_dir, 'LF')
        sim_dir = params.sim_dir

        # default_core will be changed is user passes ncore
        n_cores = args.ncore
        if n_cores != default_core:
            print("Number of cores is different from default "
                  "number of cores. Estimation will be less accurate.")

        est_core_hours, est_run_time = wc.est_LF_chours_single(
            int(params.nx), int(params.ny), int(params.nz),
            int(float(params.sim_duration) / float(params.dt)), n_cores)
        wc = shared.set_wct(est_run_time, n_cores, args.auto)

        script = write_sl_script(
            lf_sim_dir, sim_dir, srf_name, params.mgmt_db_location,
            run_time=wc, nb_cpus=n_cores)

        shared.submit_sl_script(script, 'EMOD3D', 'queued', params.mgmt_db_location,
                         srf_name, timestamp, submit_yes=submit_yes)
