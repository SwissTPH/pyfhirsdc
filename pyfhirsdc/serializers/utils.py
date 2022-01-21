from types import SimpleNamespace
import json

def read_config_file(conf):
    try:
        file = open(conf)
        json_conf = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
        file.close()
        return json_conf
    except IOError: 
           print("Error: File does not appear to exist." )
    except ValueError as e:
        print ("Config file failed to parse, please check the JSON structure")
        file.close()
        return None