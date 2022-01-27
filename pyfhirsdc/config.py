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
    if obj_conf.processor.outputDirectory is None:
        obj_conf.processor.outputDirectory = "./output"
    # check that there is worksheet defined
    if not os.path.exists(obj_conf.processor.outputDirectory):
        os.makedirs(obj_conf.processor.outputDirectory)
    if not os.path.exists(obj_conf.processor.inputFile):
        print("inputFile not found")
        return None
    processor_cfg = obj_conf.processor
    fhir_cfg = obj_conf.fhir
    return True

def get_processor_cfg():
    return processor_cfg

def get_fhir_cfg():
    return fhir_cfg

def get_defaut_fhir(resource):
    return dict_cfg['fhir'][resource]['default']