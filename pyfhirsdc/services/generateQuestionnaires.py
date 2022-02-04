"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from pyfhirsdc.models.questionnaireSDC import QuestionnaireSDC
from fhir.resources.structuremap import StructureMap
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg, get_defaut_fhir
from pyfhirsdc.converters.questionnaireItemConverter import convert_df_to_questionitems
from pyfhirsdc.serializers.json import  read_resource
import os
import json

from pyfhirsdc.utils import get_resource_path, write_resource

def generate_questionnaires(dfs_questionnaire, df_value_set, df_choiceColumn):
    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions, df_value_set, df_choiceColumn)

# @param config object fromn json
# @param name string
# @param questions DataFrame
def generate_questionnaire( name ,df_questions, df_value_set, df_choiceColumn ) :
    # try to load the existing questionnaire
    fullpath = get_resource_path("Questionnaire", name)
    print('processing quesitonnaire ', name)
    # read file content if it exists
    questionnaire = init_questionnaire(fullpath, name)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    
    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions,  df_value_set, df_choiceColumn, strategy = 'overwriteDraft')
    
    #### StructureMap ####
    
    structure_map = generate_structure_map(name, df_questions)
    questionnaire = add_structure_map(questionnaire, structure_map)
    
    # write file
    write_resource(fullpath, questionnaire, get_processor_cfg().encoding)
    

def generate_structure_map(name, df_questions):

    filepath = get_resource_path("StructureMap", name)
    structure_map = init_structure_map(filepath, name)
    write_resource(filepath, structure_map, get_processor_cfg().encoding)
    return structure_map

def add_structure_map(questionnaire, structure_map):
    if questionnaire.extension is None:
        questionnaire.extension = []

    questionnaire.extension = get_structure_map_extension(
        questionnaire.extension, 
        structure_map.url
        )
    return questionnaire


def init_structure_map(filepath, id):
    strucutred_map_json = read_resource(filepath, "StructureMap")
    default =get_defaut_fhir('StructureMap')
    if strucutred_map_json is not None :
        structure_map = StructureMap.parse_raw( json.dumps(strucutred_map_json))  
    elif default is not None:
        # create file from default
        structure_map = StructureMap.parse_raw( json.dumps(default))
        structure_map.id=id
        structure_map.name=id
        structure_map.url=get_fhir_cfg().canonicalBase\
            + "/structureMap/" \
            + get_processor_cfg().scope\
            + "-" + id


    return structure_map
    




def init_questionnaire(filepath, id):
    questionnaire_json = read_resource(filepath, "Questionnaire")
    default =get_defaut_fhir('Questionnaire')
    if questionnaire_json is not None :
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(questionnaire_json))  
    elif default is not None:
        # create file from default
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(default))
        questionnaire.id=id

    return questionnaire
    

