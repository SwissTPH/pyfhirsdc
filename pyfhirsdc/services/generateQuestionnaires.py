"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""

from pyfhirsdc.converters.structureMapConverter import add_structure_maps_url, get_structure_map_bundle
from pyfhirsdc.config import  get_processor_cfg
from pyfhirsdc.converters.questionnaireItemConverter import convert_df_to_questionitems, init_questionnaire
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
    structure_maps = get_structure_map_bundle(name, df_questions)
    #structure_maps = get_structure_maps(name, df_questions)
    questionnaire = add_structure_maps_url(questionnaire, structure_maps) 
    # write file
    write_resource(fullpath, questionnaire, get_processor_cfg().encoding)

    






