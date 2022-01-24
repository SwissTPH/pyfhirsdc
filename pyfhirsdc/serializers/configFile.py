from types import SimpleNamespace
import json
import os

def read_config_file(conf):
    try:
        file = open(conf)
        json_conf = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
        file.close()
    except IOError: 
        print("Error: File does not appear to exist." )
        return None
    except ValueError as e:
        print ("Config file failed to parse, please check the JSON structure")
        file.close()
        return None
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

