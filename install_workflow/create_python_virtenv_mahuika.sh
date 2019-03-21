#!/usr/bin/env bash
# Creates the virtual environment on mahuika for the specified environment
# This has to be run from mahuika, after create_env.sh has been run on maui!

env_path=${1?Error: "The environment path has to be given"}
name=`basename ${env_path}`

# Create virtual environment
cd ${env_path}
python3 -m venv virt_envs/python3_mahuika

# Activate new python env
source ./virt_envs/python3_mahuika/bin/activate

# Sanity check
if [[ `which python` != *"${name}"* && `which pip` != *"${name}"* ]]; then
    echo "Something went wrong, the current python used is not from the new virtual
    environment. Quitting"
    exit
fi

# Install python packages
# Using xargs means that each package is installed individually, which
# means that if there is an error (i.e. can't find qcore), then the other
# packages are still installed. However, this is slower.
xargs -n 1 -a ${env_path}/workflow/install_workflow/mahuika_python3_requirements.txt pip install

# Install qcore
pip install ./qcore