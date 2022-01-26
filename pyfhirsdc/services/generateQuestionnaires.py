from fhir.resources.questionnaire import Questionnaire
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg, get_defaut_fhir
from pyfhirsdc.converters.toQuestionnaire import convert_df_to_questionitems
from pyfhirsdc.serializers.json import get_path_or_default, read_resource
import os
import json

def generate_questionnaires(questionnaires):
    for name, questions in questionnaires.items():
        generate_questionnaire(name ,questions)

# @param config object fromn json
# @param name string
# @param questions DataFrame
def generate_questionnaire( name ,df_questions):
    # try to load the existing questionnaire
    
    filename =  "questionnaire-" + name + ".json"
    # path must end with /
    path = get_path_or_default(get_fhir_cfg().questionnaire.outputPath, "resource/quesitonnaire/")
    filepath =os.path.join(get_processor_cfg().outputDirectory , path , filename)
    print('processing quesitonnaire %s and saving it there %s', name, filepath)
    # read file content if it exists
    questionnaire = init_questionnaire(filepath)
    # clean the data frame
    df_questions = df_questions.dropna(axis=0, subset=['id'])
    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    questionnaire = convert_df_to_questionitems(questionnaire, df_questions, strategy = 'overwrite')
    # write file
    with open(filepath, 'w') as json_file:
        json_file.write(questionnaire.json())



def init_questionnaire(filepath):
    questionnaire_json = read_resource(filepath, "Questionnaire", "str")
    default =get_defaut_fhir('questionnaire')
    print (default)
    if questionnaire_json is not None :
        questionnaire = Questionnaire.parse_raw( questionnaire_json)  
    elif default is not None:
        # create file from default
        questionnaire = Questionnaire.parse_raw( json.dumps(default))

    return questionnaire
    

