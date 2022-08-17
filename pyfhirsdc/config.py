import json
import os
from pyfhirsdc.serializers.json import read_json


processor_cfg = None
fhir_cfg = None
dict_cfg = None
def read_config_file(filepath):
    global processor_cfg
    global fhir_cfg
    global dict_cfg
    obj_conf=read_json(filepath, "object")
    dict_cfg=read_json(filepath, "dict")
       # ensure the output directoy exist
    if obj_conf.processor.outputPath is None:
        obj_conf.processor.outputPath = "./output"
    # check that there is worksheet defined
    if not os.path.exists(obj_conf.processor.outputPath):
        os.makedirs(obj_conf.processor.outputPath)
    if not os.path.exists(obj_conf.processor.inputFile):
        print("inputFile {0} not found".format(obj_conf.processor.inputFile))
        return None
    processor_cfg = obj_conf.processor

    fhir_cfg = add_tail_slashes(obj_conf.fhir)
    return True

def get_processor_cfg():
    return processor_cfg

def get_fhir_cfg():
    return fhir_cfg

def get_defaut_fhir(resource):
    default_file_path =  os.path.join(dict_cfg['processor']['default_resource_path'],resource+'.json')
    if os.path.exists(default_file_path):
        json_str = read_json(default_file_path, "dict") 
        return json_str

def get_defaut_path(resource, default):
    if not resource in dict_cfg['fhir'] or dict_cfg['fhir'][resource]['outputPath'] is None:
        return os.path.join(get_processor_cfg().outputPath, default)
    return os.path.join(get_processor_cfg().outputPath, dict_cfg['fhir'][resource]['outputPath'])

def add_tail_slashes(fhir):
    if hasattr(fhir,  'canonicalBase'):
            fhir.canonicalBase= add_tail_slash(fhir.canonicalBase)
    return fhir



def add_tail_slash(url):
    return url if url is not None and url[-1:] == '/' else url + '/'
    
