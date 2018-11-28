#!/bin/bash

#get run_name from $1

if [[ $# -lt 2 ]]; then
    echo "please provide the path to sim_dir and srf_name"
    exit 1
fi

#get model list

sim_dir=$1
srf_name=$2
run_name=`python -c "from qcore import utils; d=utils.load_params('sim_params.yaml'); print d.run_name"`
lf_sim_dir=`python -c "from qcore import utils; d=utils.load_params('sim_params.yaml'); print d.lf_sim_dir"`

#check Rlog
cd $lf_sim_dir/Rlog 2> /dev/null
#abort rest of the code if cd returned not 0 (folder does not exist, emod3d has not yet been run)
if [[ $? != 0 ]]; then
    echo "$lf_sim_dir: have not yet run EMOD3D"
    exit 1
fi

rlog_count=$(expr 0) 
for rlog in *;
do
    rlog_count=`expr $rlog_count + 1`
    grep "IS FINISHED" $rlog >>/dev/null
    if [[ $? == 0 ]];
    then
        rlog_check=0
#            echo "rlog =1"
    else
        rlog_check=1
#        echo "$rlog not finsihed"
        break

    fi
done

if [[ $rlog_check == 0 ]];
then
    echo "$lf_sim_dir: EMOD3D completed"
    exit 0
else
    echo "$lf_sim_dir: EMOD3D not completed"
    exit 1
fi


