import json
import logging
import os

from pyfhirsdc.serializers.json import read_file

logger = logging.getLogger("default")

processor_cfg = None
fhir_cfg = None
dict_cfg = None
dict_df = None
used_valueset = {}
used_obs = {}
used_obs_valueset = {}
#TODO: #33 dict for used_valueset and used_valueset id + display
def append_used_valueset(idlink,label):
    if idlink not in used_valueset:
        used_valueset[idlink] = label
        
def append_used_obs_valueset(idlink,label):
    if idlink not in used_obs_valueset:
        used_obs_valueset[idlink] = label

def append_used_obs(idlink,label):
    if idlink not in used_obs:
        used_obs[idlink] = label
        
def get_used_obs():
    return used_obs

def get_used_valueset():
    return used_valueset

def get_used_obs_valueset():
    return used_obs_valueset

#        "questionnaires" : dfs_questionnaire,
#        "decisions_tables" : dfs_decision_table,
#        "valueset" : df_value_set,
#        "profile" : df_profile,
#        "extension" : df_extension,
#        "cql" : df_cql

def set_dict_df(dict_in):
    global dict_df
    dict_df = dict_in

def get_dict_df():
    return dict_df

def read_config_file(filepath):
    global processor_cfg
    global fhir_cfg
    global dict_cfg
    obj_conf=read_file(filepath, "object")
    dict_cfg=read_file(filepath, "dict")
       # ensure the output directoy exist
    if obj_conf.processor.outputPath is None:
        obj_conf.processor.outputPath = "./output"
    # check that there is worksheet defined
    if not os.path.exists(obj_conf.processor.outputPath):
        os.makedirs(obj_conf.processor.outputPath)
    if not os.path.exists(obj_conf.processor.inputFile):
        logger.error("inputFile {0} not found".format(obj_conf.processor.inputFile))
        return None
    if not hasattr(obj_conf.processor, 'layoutMode'):
        obj_conf.processor.layoutMode = 'DIRECTORY'
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
        json_str = read_file(default_file_path, "dict") 
        return json_str

def get_defaut_path(resource):
    path_parts = [get_processor_cfg().outputPath]
    RESOURCES = ['PlanDefinition', 'Questionnaire','ActivityDefinition','Library', 'StructureMap']
    VOCABULARY = ['CodeSystem', 'ConceptMap', 'ValueSet']
    if resource in RESOURCES:
        path_parts.append('resources')
    elif resource in VOCABULARY:
        path_parts.append('vocabulary')
    
    if get_processor_cfg().layoutMode == 'DIRECTORY':
        path_parts.append(resource.lower())
    
    return os.path.join(*path_parts)

def add_tail_slashes(fhir):
    if hasattr(fhir,  'canonicalBase'):
            fhir.canonicalBase= add_tail_slash(fhir.canonicalBase)
    return fhir



def add_tail_slash(url):
    return url if url is not None and url[-1:] == '/' else url + '/'
    
