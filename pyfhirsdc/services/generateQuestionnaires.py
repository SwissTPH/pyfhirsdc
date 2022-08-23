"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""

import os
from pyfhirsdc.converters.mappingConverter import add_mapping_url, get_questionnaire_mapping
from pyfhirsdc.config import  get_defaut_path, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.questionnaireItemConverter import convert_df_to_questionitems, init_questionnaire
from pyfhirsdc.serializers.librarySerializer import generate_plan_defnition_lib, write_cql_df, write_library_CQL
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource
import numpy as np

def generate_questionnaires(dfs_questionnaire, df_value_set):
    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions, df_value_set)

## generate questinnaire and questionnaire response
def generate_questionnaire( name ,df_questions, df_value_set ) :
    # try to load the existing questionnaire
    fullpath = get_resource_path("Questionnaire", name)
    fullpath_response = get_resource_path("QuestionnaireResponse", name)
    print('processing quesitonnaire {0}'.format(name))
    # read file content if it exists
    questionnaire = init_questionnaire(fullpath, name)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    

    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions,  df_value_set, strategy = 'overwriteDraft')
    #### StructureMap ####
    #structure_maps = get_structure_map_bundle(name, df_questions)
    #structure_maps = get_structure_maps(name, df_questions)
    mapping = get_questionnaire_mapping(name, df_questions)
    questionnaire = add_mapping_url(questionnaire, mapping) 
    # write file
    write_resource(fullpath, questionnaire, get_processor_cfg().encoding)
    
    
    #CQL files 
    library = generate_plan_defnition_lib(questionnaire,df_questions,'q')
    cql =write_cql_df(questionnaire, df_questions)
    if len(cql)>1:
        output_lib_path = os.path.join(
                get_processor_cfg().outputPath,
                get_fhir_cfg().Library.outputPath
            )
        output_lib_file = os.path.join(
                output_lib_path,
                "library-"+ questionnaire.id +  "." + get_processor_cfg().encoding
            )
        write_resource(output_lib_file, library, get_processor_cfg().encoding)
        cql_path = get_defaut_path('CQL', 'cql')
        write_library_CQL(cql_path, library, cql)

    






