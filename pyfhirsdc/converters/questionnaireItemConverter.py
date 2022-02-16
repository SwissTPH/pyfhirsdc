
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


import json
import numpy
from pyfhirsdc.models.questionnaireSDC import QuestionnaireItemSDC, QuestionnaireSDC
from pyfhirsdc.converters.extensionsConverter import get_calculated_expression_ext, get_checkbox_ext, get_dropdown_ext, get_candidate_expression_ext, get_choice_column_ext, get_enable_when_expression_ext, get_initial_expression_ext
from pyfhirsdc.config import get_defaut_fhir, get_processor_cfg
from pyfhirsdc.serializers.json import read_resource
from pyfhirsdc.utils import get_custom_codesystem_url, get_resource_url

def convert_df_to_questionitems(questionnaire, df_questions, df_value_set,  strategy = 'overwrite'):
    # create a dict to iterate
    dict_questions = df_questions.to_dict('index')
    # Use first part of the id (before DE) as an ID
    # questionnaire.id = list(dict_questions.keys())[0].split(".DE")[0]
    # delete all item in case of overwrite strategy
    if questionnaire.item is None or strategy == "overwrite":
        questionnaire.item =[]
    # recreate item if draft     
    for id, question in dict_questions.items():
        # pop the item if it exists
        existing_item = next((questionnaire.item.pop(index) for index in range(len(questionnaire.item)) if questionnaire.item[index].linkId == id), None)
        # create or update the item based on the strategy
        if existing_item is None\
        or strategy in ( "overwriteDraft", "overwriteDraftAddOnly" ) and\
            (existing_item.design_note is not None and "status::draft"  in existing_item.design_note):
            new_question = process_quesitonnaire_line(id, question, df_value_set,  existing_item )
            if new_question is not None:
                questionnaire.item.append(new_question)
        elif existing_item is not None:
            #put back the item if no update
            questionnaire.item.append(existing_item)
    return questionnaire

def process_quesitonnaire_line(id, question, df_value_set,  existing_item):
    new_question = None
    type = get_question_fhir_type(question)

    if type is None:
        print("${0} is not a valid type, see question ${1}".format(question['type'], id))
        return None        
    elif type == "skipped":
        return None
    # merge extensions

    #TODO manage code with custom coding system
    #TODO manage choicecolumn
    new_question = QuestionnaireItemSDC(
            linkId = id,
            type = type,
            extension = get_question_extension(question, df_value_set ),
            answerValueSet = get_question_valueset(question, df_value_set),
            design_note = "status::draft",
            text = question['description'],
            definition = get_question_definition(question)
        )
    
    return new_question

def get_question_fhir_type(question):
    # maps the pyfhirsdc type to real fhir type
    # mapping type are not in questionnaire
    fhir_type = None
    type_arr = question['type'].split(" ")
    fhir_type = type_arr[0]
    if fhir_type in ("select_one", "select_multiple"):
        fhir_type = "choice"
    elif fhir_type == "checkbox":
        fhir_type = "boolean"
    return fhir_type

def get_question_extension(question, df_value_set ):
    extensions = []
    type, detail_1, detail_2 = get_type_details(question)
    # TODO support other display than drop down
    if type.lower() == 'boolean' and isinstance(question["display"], str) and question["display"].lower() == "checkbox":
        extensions.append(get_checkbox_ext())
    elif "select_" in type and isinstance(question["display"], str) and question["display"].lower() == "dropdown" :
        extensions.append(get_dropdown_ext())
    elif "select_" in type and  isinstance(question["display"], str) and question["display"].lower() == "candidateExpression":
        extensions = get_question_choice_column(extensions, detail_1, df_value_set)
    if "enableWhenExpression" in question and question["enableWhenExpression"] is not numpy.nan:
        extensions.append(get_enable_when_expression_ext(question["enableWhenExpression"]))
    if "calculatedExpression" in question and question["enableWhenExpression"] is not numpy.nan:
        extensions.append(get_calculated_expression_ext(question["enableWhenExpression"]))
    if "initialExpression" in question and question["initialExpression"] is not numpy.nan:
        extensions.append(get_initial_expression_ext(question["initialExpression"]))
    return extensions

def get_question_valueset(question, df_value_set):
    # split question type and details
     
    type, detail_1, detail_2 = get_type_details(question)
    # split each deatil
    if "select_" in type:
        if detail_1 == "url":
            return  (detail_2)
        elif detail_2 is None  :
            # we assume it use a local valueset, TODO check if there is actual value in df_value_set
            valueset_dict = df_value_set[df_value_set['valueSet'] == detail_1]['valueSet'].unique()
            if isinstance(valueset_dict, numpy.ndarray) and len(valueset_dict)>0:
                return  get_resource_url("ValueSet", detail_1)
            else:
                print("local ValueSet ${0} not defiend in the valueset tab".format(detail_1))
                return None
    else:
        return None

def get_question_choice_column(extensions, candidate_expression, df_value_set):
    # filter DF choice column
    choice_columns = df_value_set[df_value_set['valueSet'] == candidate_expression].set_index('display').to_dict('index')
    #create extension for each field found
    for display, choice_column in choice_columns.items():
        if choice_column['code'] == '{{choiceColumn}}' and isinstance(choice_column['definition'], str):
            choice_column_details = json.loads(choice_column['definition']) 
            extension = get_choice_column_ext(choice_column_details["path"],
                display,choice_column_details["width"],choice_column_details["forDisplay"])
            if extension is not None:
                extensions.append(extension)
        elif choice_column['code'] == '{{url}}' and display is not None:
            extensions.append(get_candidate_expression_ext(candidate_expression, display))


    return extensions

def get_question_definition(question):
    # if definition == scope then build def based on canonical base, if not take the def from the xls if any
    if  question['display'] is not None and question['definition'] is not numpy.nan:
        if question['definition'].lower() == get_processor_cfg().scope.lower():
            return get_custom_codesystem_url()
        elif len(question['definition'])>5:  
            return question['definition'].lower()
        else:
            return None
    else:
        return None

def get_type_details(question):
    # structure main_type detail_1::detail_2
    type_arr = question['type'].split(" ")
    # split each details
    if len(type_arr)>1:
        detail_arr = type_arr[1].split('::')
        if len(detail_arr)>1:
            return type_arr[0], detail_arr[0], detail_arr[1]
        else:
            return type_arr[0], detail_arr[0], None
    else:
        return type_arr[0], None, None

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
    