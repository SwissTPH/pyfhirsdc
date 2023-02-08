


import json
import logging

from fhir.resources.valueset import ValueSet

from pyfhirsdc.config import get_defaut_fhir, get_dict_df, get_processor_cfg
from pyfhirsdc.converters.utils import (clean_name, get_resource_name,
                                        get_resource_url)
from pyfhirsdc.converters.valueSetConverter import (
    get_value_set_additional_data, get_value_set_compose)
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")

def generate_value_sets():
    df_value_sets = get_dict_df()
    if 'valueset' in df_value_sets:
        df_value_set = df_value_sets['valueset']
        # cleaning the DF from VS not in scope or with missing ids
        df_value_set = df_value_set[df_value_set['scope'] == get_processor_cfg().scope].dropna(axis=0, subset=['code'])
        # getting the name of the value sets
        value_sets_dict =  df_value_set['valueSet'].unique()
        # looping for each value set to get the childrens
        for name in value_sets_dict:
            generate_value_set(name, df_value_set)

def  generate_value_set(name, df_value_set):
    filepath = get_resource_path("ValueSet", name)
    logger.info('processing ValueSet {0}'.format(name))
    # read file content if it exists
    vs = init_vs(filepath)
    vs.name =  get_resource_name('ValueSet',name)
    vs.id =  clean_name(name)
    vs.url = get_resource_url('ValueSet', vs.id)
    vs.compose = get_value_set_compose(vs.compose, name, df_value_set)
    vs = get_value_set_additional_data(vs,  df_value_set[df_value_set['valueSet'] == name ])
    write_resource(filepath, vs, get_processor_cfg().encoding)

def init_vs(filepath):
    vs_json = None#read_resource(filepath, "ValueSet")
    default =get_defaut_fhir('ValueSet') 
    if vs_json is not None :
        vs = ValueSet.parse_raw( json.dumps(vs_json))  
    elif default is not None:
        # create file from default
        vs = ValueSet.parse_raw( json.dumps(default))
    else: 
        vs = ValueSet.construct()   
    #if get_fhir_cfg().publisher is not None:
    #    vs.publisher = str(get_fhir_cfg().publisher),
    #if get_fhir_cfg().copyright is not None:
    #    vs.copyright = str(get_fhir_cfg().copyright),
    #if get_fhir_cfg().status is not None: 
    #    vs.status = Code(get_fhir_cfg().status),
    return vs

    