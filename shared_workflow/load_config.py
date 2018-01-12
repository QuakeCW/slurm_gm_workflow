
import sys
import os
import json

def load(directory=os.path.dirname(os.path.abspath(__file__)), cfg_name="workflow_config.json"):
    #directory = os.path.dirname(os.path.abspath(__file__))
    print directory
    #config_file = os.path.join(directory, "workflow_config.json")
    config_file = os.path.join(directory, cfg_name)
    try:
        with open(config_file) as f:
            config_dict = json.load(f)
            return config_dict

    except IOError:
        print "No %s available on %s" %(cfg_name,directory)
        print "This is a fatal error. Please contact someone from the software team."
        exit(1)


