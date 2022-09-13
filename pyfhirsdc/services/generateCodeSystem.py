"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import json
import os
from pyfhirsdc.config import get_defaut_fhir, get_defaut_path, get_dict_df,  get_processor_cfg
from pyfhirsdc.converters.codeSystemConverter import  generate_observation_concept, generate_questionnaire_concept, generate_valueset_concept
from pyfhirsdc.converters.valueSetConverter import add_concept_in_valueset_df
from pyfhirsdc.serializers.json import  read_resource
from fhir.resources.codesystem import CodeSystem
from fhir.resources.library import Library

from pyfhirsdc.serializers.librarySerializer import get_observation_cql_from_valueset, write_library_CQL
from pyfhirsdc.serializers.utils import  get_resource_path 
from pyfhirsdc.converters.utils import clean_group_name,  get_codableconcept_code, get_custom_codesystem_url, get_resource_url


def generate_custom_code_system(dfs_questionnaire, df_value_set):
    concept = []
    for name, df_questions in dfs_questionnaire.items():
        question_concept = generate_questionnaire_concept(df_questions)
        if len(question_concept)>0:
           concept = concept +  question_concept
    valueset_concept = generate_valueset_concept(df_value_set)
    if len(valueset_concept)>0:
        concept = concept +  valueset_concept

    
    # path must end with /
    
    # create directory if not exists
    name_cs = get_processor_cfg().scope.lower()
    filepath = get_resource_path("CodeSystem",name_cs )

    print('processing codeSystem {0}'.format( name_cs))
    # read file content if it exists
    code_system = init_code_system(filepath)
    code_system.concept = concept
    code_system.name = name_cs

    # write file
    with open(filepath, 'w',  encoding="utf-8") as json_file:
        json_file.write(code_system.json( indent=4))
        #TODO use configuration


def generate_observation_valueset_libs():
    dfs_questionnaire = get_dict_df()['questionnaires']
    concepts = []
    name_vs = get_processor_cfg().scope + "Observation"
    for name, df_questions in dfs_questionnaire.items():
        question_concept = generate_observation_concept(df_questions)
        if len(question_concept)>0:
           concepts = concepts +  question_concept
    if len(concepts)>0:    
        add_concept_in_valueset_df('observation', concepts)


        lib = Library(
            status= 'active',
            id=clean_group_name(name_vs),
            name=name_vs,
            url = get_resource_url('Library', clean_group_name(name_vs)),
            type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'
        ))
        
        cql = get_observation_cql_from_valueset(concepts, lib)
        cql_path = get_defaut_path('CQL', 'cql')
        write_library_CQL(cql_path, lib, cql)
            
            
        #TODO use configuration
    
    #FIXME generate_diagnosis_concept
    #FIXME generate_observation_concept
    #FIXME generate_condition_concept    
    
   


    


def init_code_system(filepath):
    code_system_json = read_resource(filepath, "CodeSystem")
    default =get_defaut_fhir('CodeSystem')
    #if code_system_json is not None :
    #    code_system = CodeSystem.parse_raw( json.dumps(code_system_json))  
    #elif default is not None:
    #    # create file from default
    code_system = CodeSystem.parse_raw( json.dumps(default))
    CodeSystem.url = get_custom_codesystem_url()

     

    return code_system    