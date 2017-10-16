# TODO: import the CONFIG here

import glob
import os.path
import sys
import os

# TODO: this needs to append the path to qcore as well
qcore_path = '/projects/nesi00213/qcore'
sys.path.append(qcore_path)
from shared import *
# TODO: remove this once temp_shared is gone
from temp_shared import resolve_header

sys.path.append(os.getcwd())

print(sys.path)

import install

#section for parser to determine if using automate wct
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("auto",nargs="?",type=str)
args = parser.parse_args()


def confirm(q):
    show_horizontal_line
    print q
    return show_yes_no_question()

def create_ll(submit_yes):
    from params_base import tools_dir

    execfile(os.path.join(bin_process_dir,"set_runparams.py"))
    glob.glob('LF/*')
    lf_sim_dirs=glob.glob('LF/*')
    f_template=open('run_emod3d.ll.template')
    template=f_template.readlines()
    template
    str_template=''.join(template)

    for lf_sim_dir in lf_sim_dirs:
        txt=str_template.replace("$lf_sim_dir",lf_sim_dir).replace("$tools_dir",tools_dir)
        if wall_clock_limit != '':
            txt=txt.replace("4:00:00", wall_clock_limit)
        rup_mod = lf_sim_dir.split('/')[1]
        txt=txt.replace("$rup_mod",rup_mod)
        fname_llscript='run_emod3d_%s.ll'%rup_mod
        f_llscript=open(fname_llscript,'w')
        f_llscript.write('# script version: %s\n'%bin_process_ver)
        f_llscript.write(txt)
        f_llscript.close()
        print "Loadleveler script %s written" %fname_llscript
        if submit_yes:
            print "Submitting %s" %fname_llscript
            res=exe("llsubmit %s"%fname_llscript,debug=False)
            #print res
        else:
            print "User chose to submit the job manually"

def create_sl(submit_yes):
    from params_base import tools_dir

    execfile(os.path.join(bin_process_dir, "set_runparams.py"))
    glob.glob('LF/*')
    lf_sim_dirs = glob.glob('LF/*')
    f_template = open('run_emod3d.sl.template')
    template = f_template.readlines()
    str_template = ''.join(template)

    for lf_sim_dir in lf_sim_dirs:
        txt = str_template.replace("{{lf_sim_dir}}", lf_sim_dir).replace("{{tools_dir}}", tools_dir)
        rup_mod = lf_sim_dir.split('/')[1]
        fname_slurm_script = 'run_emod3d_%s.sl' % rup_mod
        f_sl_script = open(fname_slurm_script, 'w')

        # slurm header
        # TODO: change this values to values that make more sense
        nb_cpus = "128"
        run_time = "1:00:00"
        job_name = "emod3d_%s" % rup_mod
        memory = "16G"
        header = resolve_header("nesi00213",nb_cpus,run_time,job_name,bin_process_ver, memory,
                                job_description="emod3d slurm script", additional_lines="#SBATCH -C avx")

        f_sl_script.write(header)
        f_sl_script.write(txt)
        f_sl_script.close()
        print "Slurm script %s written" % fname_slurm_script
        if submit_yes:
            print "Submitting %s" % fname_slurm_script
            res = exe("sbatch %s" % fname_slurm_script, debug=False)
            # print res
        else:
            print "User chose to submit the job manually"


if args.auto == 'auto':
    print "This feature is disabled for slurm scripts"
    exit(1)

    # TODO: prepare an auto submit for slurm scripts
    import wct
    
    try:
        import params
    except:
        print "import params.py failed. check sys.path"
    else:
        # TODO: get some values for when DB is empty
        db = wct.WallClockDB()
        nx = int(params.nx)
        ny = int(params.ny)
        nz = int(params.nz)
        sim_duration = int(float(params.sim_duration))
        num_procs = int(params.n_proc)
        est = db.estimate_wall_clock_time(nx,ny,nz,sim_duration,num_procs)
        est_max=est[0]
        wall_clock_limit=est_max

        create_ll(submit_yes=True)
else:

    #install.wallclocl returns a datetime type value, transform it into string
    wall_clock_limit = str(install.wallclock('.'))

    submit_yes = confirm("Also submit the job for you?")
    
    create_sl(submit_yes)
