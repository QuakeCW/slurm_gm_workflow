# TODO: change this to come from a config
# bin_process_path='/nesi/projects/nesi00213/workflow'
bin_process_path = '/projects/nesi00213/workflow'
import glob
import os.path
import sys
from version import *
import math

# TODO: remove this once temp_shared is gone
from temp_shared import resolve_header

bin_process_dir = os.path.join(bin_process_path, bin_process_ver)
sys.path.append(bin_process_dir)

# TODO: add qcore to the python path
sys.path.append('/projects/nesi00213/qcore')

from shared import *

sys.path.append(os.getcwd())
from params_base import tools_dir

# TODO: hardcoding is bad!
max_tasks_per_node = "12"


def confirm(q):
    show_horizontal_line
    print q
    return show_yes_no_question()

#print version
#print VERSION

merge_ts_name_prefix = "post_emod3d_merge_ts"
winbin_aio_name_prefix = "post_emod3d_winbin_aio"

glob.glob('LF/*')
lf_sim_dirs = glob.glob('LF/*')
print lf_sim_dirs
# reading merge_ts_template
merge_ts_template = open('%s.sl.template' % merge_ts_name_prefix)
merge_ts_template_contents = merge_ts_template.readlines()
merge_ts_str_template = ''.join(merge_ts_template_contents)
# reading winbin_aio_template
winbin_aio_template = open('%s.sl.template' % winbin_aio_name_prefix)
winbin_aio_template_contents = winbin_aio_template.readlines()
winbin_aio_str_template = ''.join(winbin_aio_template_contents)

submit_yes = confirm("Also submit the job for you?")

for lf_sim_dir in lf_sim_dirs:
    print "Working on", lf_sim_dir
    # preparing merge_ts submit
    txt = merge_ts_str_template.replace("{{lf_sim_dir}}", lf_sim_dir)
    try:
        txt = txt.replace("{{tools_dir}}", tools_dir)
    except:
        print "**error while replacing tools_dir**"

    outbin = os.path.join(lf_sim_dir, 'OutBin')
    seis_files = glob.glob(os.path.join(outbin, '*seis*.e3d'))
    n_seis = len(seis_files)

    rup_mod = lf_sim_dir.split('/')[1]

    # TODO: change this values to values that make more sense
    nb_cpus = max_tasks_per_node
    run_time = "00:30:00"
    job_name = "post_emod3d_merge_ts_%s" % rup_mod
    memory = "16G"
    header = resolve_header("nesi00213", nb_cpus, run_time, job_name, bin_process_ver, memory,
                            job_description="post emod3d: merge_ts", additional_lines="#SBATCH -C avx")

    fname_merge_ts_script = '%s_%s.sl' % (merge_ts_name_prefix, rup_mod)
    final_merge_ts = open(fname_merge_ts_script, 'w')
    final_merge_ts.write(header)
    final_merge_ts.write(txt)
    final_merge_ts.close()
    print "Slurm script %s written" % fname_merge_ts_script

    # preparing winbin_aio
    txt = winbin_aio_str_template.replace("{{lf_sim_dir}}", lf_sim_dir)
    # TODO: change this values to values that make more sense
    nb_cpus = "1"
    run_time = "00:30:00"
    job_name = "post_emod3d_winbin_aio_%s" % rup_mod
    memory = "16G"
    header = resolve_header("nesi00213", nb_cpus, run_time, job_name, bin_process_ver, memory,
                            job_description="post emod3d: winbin_aio", additional_lines="#SBATCH -C avx")

    fname_winbin_aio_script = '%s_%s.sl' % (winbin_aio_name_prefix, rup_mod)
    final_winbin_aio = open(fname_winbin_aio_script, 'w')
    final_winbin_aio.write(header)
    final_winbin_aio.write(txt)
    final_winbin_aio.close()
    print "Slurm script %s written" % fname_winbin_aio_script

    if submit_yes:
        print "Submitting not implemented yet!"
        #res = exe("llsubmit %s" % fname_llscript, debug=False)
    #        print res
    else:
        print "User chose to submit the job manually"
