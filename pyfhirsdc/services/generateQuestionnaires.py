"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""
from pyfhirsdc.models.questionnaireSDC import QuestionnaireSDC
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg, get_defaut_fhir
from pyfhirsdc.converters.questionnaireConverter import convert_df_to_questionitems
from pyfhirsdc.serializers.json import get_path_or_default, read_resource
import os
import json

from pyfhirsdc.utils import write_resource

def generate_questionnaires(dfs_questionnaire, df_value_set, df_choiceColumn):
    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions, df_value_set, df_choiceColumn)

# @param config object fromn json
# @param name string
# @param questions DataFrame
def generate_questionnaire( name ,df_questions, df_value_set, df_choiceColumn ) :
    # try to load the existing questionnaire
    
    filename =  "questionnaire-" + name + ".json"
    # path must end with /
    path = get_path_or_default(get_fhir_cfg().questionnaire.outputPath, "resource/quesitonnaire/")
    # create directory if not exists
    fullpath = os.path.join(get_processor_cfg().outputDirectory , path )
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)

    filepath =os.path.join(fullpath , filename)
    print('processing quesitonnaire ', name)
    # read file content if it exists
    questionnaire = init_questionnaire(filepath, name)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id']).set_index('id')
    
    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions,  df_value_set, df_choiceColumn, strategy = 'overwriteDraft')
    # write file
    write_resource(fullpath, questionnaire, 'json')
    with open(filepath, 'w') as json_file:
        json_file.write(questionnaire.json( indent=4))



def init_questionnaire(filepath, id):
    questionnaire_json = read_resource(filepath, "Questionnaire")
    default =get_defaut_fhir('questionnaire')
    if questionnaire_json is not None :
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(questionnaire_json))  
    elif default is not None:
        # create file from default
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(default))
        questionnaire.id=id

    return questionnaire
    

