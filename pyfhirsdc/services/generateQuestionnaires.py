"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""

import logging

import numpy as np

from pyfhirsdc.config import get_dict_df, get_processor_cfg
from pyfhirsdc.converters.mappingConverter import (add_mapping_url,
                                                   get_questionnaire_mapping)
from pyfhirsdc.converters.questionnaireItemConverter import (
    convert_df_to_questionitems, get_timestamp_item, init_questionnaire,
    validate_fhirpath)
from pyfhirsdc.converters.utils import inject_sub_questionnaires
from pyfhirsdc.serializers.http import post_files
from pyfhirsdc.serializers.librarySerializer import generate_attached_library
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")

def generate_questionnaires():
    dfs_questionnaire = get_dict_df()['questionnaires']

    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions)

## generate questinnaire and questionnaire response
def generate_questionnaire( name ,df_questions) :
    
    # try to load the existing questionnaire
    fullpath = get_resource_path("Questionnaire", name)
    logger.info('processing questionnaire {0}'.format(name))
    # read file content if it exists
    questionnaire = init_questionnaire(fullpath, name)
    # clean the data frame
    
    
    df_questions = inject_sub_questionnaires(df_questions)
    df_questions_item = df_questions[df_questions.type != 'mapping']
    df_questions_lib = df_questions
    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions_item)
        # add timestamp
    questionnaire.item.append(get_timestamp_item())
    #### StructureMap ####
    

    #structure_maps = get_structure_map_bundle(name, df_questions)
    #structure_maps = get_structure_maps(name, df_questions)
    mapping = get_questionnaire_mapping(name, df_questions_lib)
    questionnaire = add_mapping_url(questionnaire, mapping)
    library = generate_attached_library(questionnaire,df_questions_lib,'q')

    # write file
    write_resource(fullpath, questionnaire, get_processor_cfg().encoding)
    #CQL files 
    if get_processor_cfg().fhirpath_validator is not None:
        post_files(fullpath, get_processor_cfg().fhirpath_validator)
    






