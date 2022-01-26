from types import SimpleNamespace
import json
import os

def read_config_file(conf):
    json_conf=read_json(filepath)
       # ensure the output directoy exist
    if json_conf.processor.outputDirectory is None:
        json_conf.processor.outputDirectory = "./output"
    # check that there is worksheet defined
    if not os.path.exists(json_conf.processor.outputDirectory):
        os.makedirs(json_conf.processor.outputDirectory)
    if not os.path.exists(json_conf.processor.inputFile):
        print("inputFile not found")
        return None

    return json_conf

def read_json(filepath):
    try:
        file = open(filepath)
        json = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
        file.close()
    except IOError: 
        print("Error: File %s does not appear to exist.", filepath )
        return None
    except ValueError as e:
        print ("file %s failed to parse, please check the JSON structure", filepath)
        file.close()
        return None
    return json

def read_resource(filepath, resource):
    resource=read_json(filepath)
    # check if the resource has the right type
    if resource is not None and  (resource.resourceType == resource ):
        return resource
    else:
        return None

def get_slash_ending_path(path, default):
    if len(path)>0:
        path = path if path[:-1] == '/' else path + '/'
    else:
        path = default