#!/bin/bash
# script version: {{version}}
# {{job_description}}

# Please modify this file as needed, this is just a sample
#PBS -N clean_up
#PBS -V
#PBS -q normal
#PBS -A inhouse
#PBS -l select=1:ncpus=1
#PBS -l walltime=00:30:00
#PBS -W sandbox=PRIVATE

module purge
module add intel/18.0.3 impi/18.0.3 craype-network-opa craype-mic-knl
export gmsim_root=/home01/hpc11a02/gmsim
export PYTHONPATH=$gmsim_root/Environments/nurion/workflow
source $gmsim_root/Environments/nurion/virt_envs/python3_nurion/bin/activate
export SLURM_JOB_ID="${PBS_JOBID/.pbs/}"

## qsub supply the following variables with -v option
#SIM_DIR=$1
#SRF_NAME=$2
#MGMT_DB_LOC=$3

script_start=`date`
echo "script started running at: $script_start"
runtime_fmt="%Y-%m-%d_%H:%M:%S"
timestamp=`date +%Y%m%d_%H%M%S`

start_time=`date +${runtime_fmt}`
echo ___cleaning up___


python $gmsim/workflow/scripts/cybershake/add_to_mgmt_queue.py $MGMT_DB_LOC/mgmt_db_queue $SRF_NAME clean_up running $SLURM_JOB_ID
rm -r $SIM_DIR/LF/Restart
res=`python $gmsim/workflow/scripts/clean_up.py $SIM_DIR`
exit_val=$?

end_time=`date +$runtime_fmt`
echo $end_time

if [[ $exit_val == 0 ]]; then
    #passed

    python $gmsim/workflow/scripts/cybershake/add_to_mgmt_queue.py $MGMT_DB_LOC/mgmt_db_queue $SRF_NAME clean_up completed $SLURM_JOB_ID

    #save meta data
    python $gmsim/workflow/metadata/log_metadata.py $SIM_DIR clean_up start_time=$start_time end_time=$end_time

else
    python $gmsim/workflow/scripts/cybershake/add_to_mgmt_queue.py $MGMT_DB_LOC/mgmt_db_queue $SRF_NAME clean_up failed $SLURM_JOB_ID --error "$res"
fi
