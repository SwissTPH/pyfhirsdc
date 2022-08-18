from pathlib import Path
from types import SimpleNamespace
import json
import os

def read_file(filepath, type = "object"):
    json_str = None
    try:
        file = open(filepath, 'r',  encoding="utf-8")
        if type == "object":
            json_str = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
        elif type == "str":
            json_str = file.read()
        elif type == "dict":
            json_str = json.load(file)
            
        file.close()
    except IOError: 
        raise IOError("Error: File {0} does not appear to exist.".format(filepath))
    except ValueError as e:
        raise ValueError("file {0} failed to parse, please check the JSON structure".format(filepath))
    return json_str

def read_resource(filepath, resource):
    resource_dict = read_file(filepath, 'dict') if os.path.exists(filepath) else None

    # check if the resource has the right type 
    if resource_dict is not None and 'resourceType' in resource_dict\
        and (resource_dict['resourceType'] == resource  or resource == 'any'):
        return resource_dict
    else:
        return None

