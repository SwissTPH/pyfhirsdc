"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import json
import os

from fhir.resources.attachment import Attachment
from fhir.resources.codesystem import CodeSystem
from fhir.resources.library import Library

from pyfhirsdc.config import (get_defaut_fhir, get_defaut_path, get_dict_df,
                              get_processor_cfg)
from pyfhirsdc.converters.codeSystemConverter import (
    generate_observation_concept, generate_questionnaire_concept,
    generate_valueset_concept)
from pyfhirsdc.converters.utils import (clean_group_name,
                                        get_codableconcept_code,
                                        get_custom_codesystem_url,
                                        get_resource_url)
from pyfhirsdc.converters.valueSetConverter import add_concept_in_valueset_df
from pyfhirsdc.serializers.json import read_resource
from pyfhirsdc.serializers.librarySerializer import (
    get_observation_cql_from_concepts, get_valueset_cql_from_concepts,
    write_library_CQL)
from pyfhirsdc.serializers.utils import get_resource_path, write_resource


def generate_custom_code_system():
    dfs_questionnaire = get_dict_df()['questionnaires']
    df_value_set = get_dict_df()['valueset'].dropna(axis=0, subset=['scope'])
    concept = []
    obs_concepts = []
    question_concepts = []
    valueset_concepts = []
    for name, df_questions in dfs_questionnaire.items():
        question_concept = generate_questionnaire_concept(df_questions)
        obs_concept= generate_observation_concept(df_questions)
        if len(question_concept)>0:
           question_concepts +=   question_concept
        if len(obs_concept):
            obs_concepts+=obs_concept
    if len(question_concepts)>0:
        concept =  question_concepts    
    valueset_concepts, obs_val_concepts = generate_valueset_concept(df_value_set)
    if len(valueset_concepts)>0:
        concept = concept +  valueset_concepts
    if len(obs_val_concepts)>0:
        obs_concepts +=  obs_val_concepts
        concept = concept +  obs_concepts        
    generate_valuset_valueset_libs(valueset_concepts)
    generate_observation_valueset_libs(obs_concepts)
    
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


def  generate_valuset_valueset_libs(valueset_concepts):
    if len(valueset_concepts)>0:    
    # Generate library to resolve "display to code"
        name_vs = get_processor_cfg().scope.lower() + "valueset"
        lib_id = clean_group_name(name_vs)
        lib = Library(
            status= 'active',
            id=lib_id,
            name=name_vs,
            url = get_resource_url('Library', clean_group_name(name_vs)),
            type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'),
            content =[Attachment(
                id = "ig-loader-" + name_vs + ".cql"
            )])
        
        cql = get_valueset_cql_from_concepts(valueset_concepts, lib)
        cql_path = get_defaut_path('CQL', 'cql')
        lib_path =get_resource_path('Library', name_vs )
        write_library_CQL(cql_path, lib, cql)
        write_resource(lib_path, lib)

def generate_observation_valueset_libs(question_concepts):

    name_vs = get_processor_cfg().scope.lower() + "observation"
    #for name, df_questions in dfs_questionnaire.items():
    #    question_concept = generate_observation_concept(df_questions)
    #    if len(question_concept)>0:
    #       concepts = concepts +  question_concept
    if len(question_concepts)>0:    
        

        lib_id = clean_group_name(name_vs)
        lib = Library(
            status= 'active',
            id=lib_id,
            name=name_vs,
            url = get_resource_url('Library', clean_group_name(name_vs)),
            type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'),
            content =[Attachment(
                id = "ig-loader-" + name_vs + ".cql"
            )])
        
        cql = get_observation_cql_from_concepts(question_concepts, lib)
        add_concept_in_valueset_df('observation', question_concepts)
        cql_path = get_defaut_path('CQL', 'cql')
        lib_path =get_resource_path('Library', name_vs )
        write_library_CQL(cql_path, lib, cql)
        write_resource(lib_path, lib)
            
        #TODO use configuration
        
    #FIXME generate_valusetLib
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