bin_process_path = '/nesi/projects/nesi00213/workflow'
import glob
import os.path
import sys

sys.path.append(os.path.abspath(os.path.curdir))
from params import *
from params_base_bb import *
# TODO: move this to qcore library
from temp_shared import resolve_header
from shared import *


def confirm(q):
    show_horizontal_line
    print q
    return show_yes_no_question()


def submit_sl_script(script_name):
    print "Submitting %s is not yet implemented" % script_name
    pass


def create_sl(bb_sim_dirs, sl_template_prefix, submit_yes):
    pass
    f_template = open('%s.sl.template' % sl_template_prefix)
    template = f_template.readlines()
    template
    str_template = ''.join(template)

    for bb_sim_dir in bb_sim_dirs:
        txt = str_template.replace("$bb_sim_dir", bb_sim_dir)

        #    variation = '_'.join(bb_sim_dir.split('/')[0:2])
        variation = bb_sim_dir.replace(bb_dir + '/', '').replace('/', '__')
        print variation
        txt = txt.replace("$rup_mod", variation)
        fname_slscript = '%s_%s.sl' % (sl_template_prefix, variation)
        f_slscript = open(fname_slscript, 'w')
        # TODO: change this values to values that make more sense or come from somewhere
        nb_cpus = "24"
        run_time = "00:30:00"
        job_name = "sim_bb_%s" % variation
        memory = "16G"
        header = resolve_header("nesi00213", nb_cpus, run_time, job_name, version="slurm", memory=memory,
                                job_description="BB calculation", additional_lines="#SBATCH -C avx")
        f_slscript.write(header)
        f_slscript.write(txt)
        f_slscript.close()
        print "Slurm script %s written" % fname_slscript
        if submit_yes:
            submit_sl_script(fname_slscript)

        else:
            print "User chose to submit the job manually"


version = 'SERIAL'
if len(sys.argv) == 2:
    version = sys.argv[1]
    if version == 'MPI':
        ll_name_prefix = 'run_bb_mpi'
    else:
        print '%s is an invalid option' % version
        version = 'SERIAL'
        print 'Set to default %s' % version
if version == 'SERIAL':
    ll_name_prefix = 'run_bb'

print version

import fnmatch
import os

bb_sim_dirs = []
bb_sim_dirs_to_skip = []
file_to_find = 'params_bb_uncertain.py'
for root, dirnames, filenames in os.walk(bb_dir):
    for filename in fnmatch.filter(filenames, file_to_find):
        if v_mod_1d_name not in root:
            bb_sim_dirs_to_skip.append(root)
        else:
            bb_sim_dirs.append(root)
print bb_sim_dirs
if len(bb_sim_dirs_to_skip) > 0:
    print "BB subdirectories to skip: ", bb_sim_dirs_to_skip
    print "Note: Run install_bb.py again to process these"

# f_template=open('%s.ll.template'%ll_name_prefix)
# template=f_template.readlines()
# template
# str_template=''.join(template)

submit_yes = confirm("Also submit the job for you?")

create_sl(bb_sim_dirs, ll_name_prefix, submit_yes)
