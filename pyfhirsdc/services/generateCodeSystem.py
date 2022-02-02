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
from pyfhirsdc.serializers.json import get_path_or_default, read_resource
from fhir.resources.codesystem import CodeSystem

def generate_custom_code_system(dfs_questionnaire, df_value_set):
    concept = []
    for name, df_questions in dfs_questionnaire.items():
        question_concept = generate_questionnaire_concept(df_questions)
        if len(question_concept)>0:
           concept = concept +  question_concept
    valueset_concept = generate_valueset_concept(df_value_set)
    if len(valueset_concept)>0:
          concept = concept +  valueset_concept

    filename =  "codesystem-" + get_processor_cfg().scope.lower() + ".json"
    # path must end with /
    path = get_path_or_default(get_fhir_cfg().codeSystem.outputPath, "vocabulary/codesystem/")
    # create directory if not exists
    fullpath = os.path.join(get_processor_cfg().outputDirectory , path )
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)

    filepath =os.path.join(fullpath , filename)
    print('processing codeSystem ', name)
    # read file content if it exists
    code_system = init_code_system(filepath)
    code_system.concept = concept

    # write file
    with open(filepath, 'w') as json_file:
        json_file.write(code_system.json( indent=4))

def init_code_system(filepath):
    code_system_json = read_resource(filepath, "CodeSystem")
    default =get_defaut_fhir('codeSystem')
    if code_system_json is not None :
        code_system = CodeSystem.parse_raw( json.dumps(code_system_json))  
    elif default is not None:
        # create file from default
        code_system = CodeSystem.parse_raw( json.dumps(default))
        CodeSystem.url = get_fhir_cfg().canonicalBase + "/CodeSystem/emc-custom-codes-codes"

     

    return code_system    