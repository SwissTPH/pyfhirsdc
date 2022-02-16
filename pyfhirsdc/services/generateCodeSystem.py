"""
    Service to generate the custom codeSystem ressource
    needs the sheet:
        - q.X
        - valueSet
"""

import json
import os
from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.codeSystemConverter import generate_questionnaire_concept, generate_valueset_concept
from pyfhirsdc.serializers.json import  read_resource
from fhir.resources.codesystem import CodeSystem

from pyfhirsdc.utils import get_custom_codesystem_url, get_resource_path, get_resource_url


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

    filepath = get_resource_path("CodeSystem", get_processor_cfg().scope.lower())


    print('processing codeSystem {0}'.format( get_processor_cfg().scope.lower()))
    # read file content if it exists
    code_system = init_code_system(filepath)
    code_system.concept = concept

    # write file
    with open(filepath, 'w') as json_file:
        json_file.write(code_system.json( indent=4))

def init_code_system(filepath):
    code_system_json = read_resource(filepath, "CodeSystem")
    default =get_defaut_fhir('CodeSystem')
    if code_system_json is not None :
        code_system = CodeSystem.parse_raw( json.dumps(code_system_json))  
    elif default is not None:
        # create file from default
        code_system = CodeSystem.parse_raw( json.dumps(default))
        CodeSystem.url = get_custom_codesystem_url()

     

    return code_system    