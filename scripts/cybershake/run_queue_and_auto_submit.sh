#!/bin/bash

if [[ $# -lt 2 ]];then
    echo "please provide the path to the root folder of runs and sleep interval(seconds)"
    echo "./run_queue_and_submit.sh /nesi/nobackup/nesi00213/RunFolder/Cybershake/v18p5/ 60"
    exit 1
fi

path_sim_root=$1
interval=$2
trap "echo Exited!; exit;" SIGINT SIGTERM

while [ 1 ];
do
    #run the commands queued up first, before submit
    cmd="$gmsim/workflow/scripts/cybershake/run_db_queue.sh $path_sim_root"
    echo $cmd
    $cmd

    cmd="python $gmsim/workflow/scripts/cybershake/auto_submit.py $path_sim_root"
    echo $cmd
    $cmd
    sleep $interval
done