#!/bin/bash

if [[ $# -lt 2 ]];then
    echo "please provide the list of vms to install, and path to cybershake folder"
    echo "install_cybershake.sh /path/to/cybershake/root/ /path/to/list_vms"
    exit 1
fi

script_location=`dirname $0`

cybershake_root=$1

sim_root_dir=$cybershake_root/Runs
vm_root_dir=$cybershake_root/Data/VMs


#get list of VM
#cd $vm_root_dir
list_vm=`cat $2`
echo $list_vm

#each vm match with multiple srf
for vm in $list_vm;
do
    echo $vm | python $script_location/install_cybershake.py $cybershake_root
done

#list_source='ls 
#echo $sim_root_dir