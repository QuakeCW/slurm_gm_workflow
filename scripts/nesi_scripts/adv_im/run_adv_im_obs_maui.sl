#!/bin/bash
# script version: slurm
# im_calc
#

# Please modify this file as needed, this is just a sample
#SBATCH --account=nesi00213
#SBATCH --ntasks=40
#SBATCH --time=24:00:00
#SBATCH --output im_calc_%j_%x.out
#SBATCH --error im_calc_%j_%x.err
#SBATCH --nodes=1
#SBATCH --hint=nomultithread
#SBATCH --exclusive

export IMPATH=$gmsim/IM_calculation/IM_calculation/scripts
export PYTHONPATH=$gmsim/qcore:/$PYTHONPATH:$IMPATH

if [[ $# -lt 2 ]];
then
    echo "please provide 1. path to obs_dir 2. list of event names"
    exit 1
fi

obs_dir=$1
list_event=$2
opensees_bin=${3:-/nesi/project/nesi00213/opt/maui/tmp/OpenSees}

for event in `cat $list_event | awk '{print $1}'`;
do 
    echo $event
    path_eventBB=$obs_dir/$event/*/*/accBB
    path_IM_calc=$obs_dir/IM_calc
    path_event_out=$path_IM_calc/$event
    # tests before starting analysis if the csv is already there
    # get station count
    station_count=`ls $path_eventBB | cut -d. -f1 | sort -u | wc -l`
    if [[ $station_count -lt 0 ]]; then
        echo failed to get the station count in $path_eventBB
        exit 2
    fi
    # get module names used for simulation analysis
    root_params=`realpath $obs_dir/../Runs/root_params.yaml`
    if [[ $? == 0 ]] && [[ -f $root_params ]]; then
        adv_IM_models=`python -c "from qcore.utils import load_yaml; params=load_yaml('$root_params'); print(' '.join(params['advanced_IM']['models']));"`
    else
    #failed to find a model from config/yaml
        continue
    fi
    # run for all Models
    for adv_IM_model in $adv_IM_models;
    do
        # re-initialize flag
        run_im=0
        # check if csv pre-exist
        # skip if exist
        # python $gmsim/workflow/scripts/im_calc_checkpoint.py $path_IM_calc $station_count --event_name $event --observed
        adv_IM_csv=$path_event_out/$adv_IM_model\.csv
        if [[ -f $adv_IM_csv ]]; then
            #check for station count
            csv_station_count=`python -c "import pandas as pd; df = pd.read_csv('$adv_IM_csv'); print(len(sorted(set(df.station))))"`
            if [[ $csv_station_count != station_count ]];then
                # previous run may be corrupted, remove the old csv.
                rm $adv_IM_csv
                run_im=1
            fi
        else
            run_im=1
        fi
        if [[ $run_im == 1 ]]; then
            time python $IMPATH/calculate_ims.py $path_eventBB a -o $path_event_out -np 40 -i $event -r $event -t  o -e -a $adv_IM_model --OpenSees_path $opensees_bin 
            python $gmsim/workflow/scripts/verify_adv_IM.py $path_event_out $adv_IM_model  
            res=$?
            if [[ res != 0 ]];then
                # tes failed
                echo $event >> $obs_dir/../list_done_$adv_IM_model
            else
                echo "something went wrong, stopping the job, check logs for $path_event_out for $adv_IM_model"
                exit 3
            fi
        fi
    done
done