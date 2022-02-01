from types import SimpleNamespace
import json
import os




def read_json(filepath, type = "object"):
    json_str = None
    try:
        file = open(filepath)
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
    resource_dict=read_json(filepath, 'dict') if os.path.exists(filepath) else None
    # check if the resource has the right type 
    if resource_dict is not None and (resource_dict['resourceType'] == resource ):
        return resource_dict
    else:
        return None



def get_path_or_default(path, default):
    if len(path)>0:
        path = path if path[:-1] == '/' else path + '/'
    else:
        path = default
    return path