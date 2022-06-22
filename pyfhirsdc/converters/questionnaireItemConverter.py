
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


import json
import numpy
from pyfhirsdc.models.questionnaireSDC import QuestionnaireItemSDC, QuestionnaireSDC
from pyfhirsdc.models.questionnaireResponseSDC import QuestionnaireResponseItemSDC, QuestionnaireResponseSDC
from pyfhirsdc.converters.extensionsConverter import get_calculated_expression_ext, get_checkbox_ext, get_dropdown_ext, get_candidate_expression_ext, get_choice_column_ext, get_enable_when_expression_ext, get_initial_expression_ext
from pyfhirsdc.config import get_defaut_fhir, get_processor_cfg
from pyfhirsdc.serializers.json import read_resource
from pyfhirsdc.converters.utils import clean_name, get_custom_codesystem_url, get_resource_url
import pandas as pd

def convert_df_to_questionitems(questionnaire, questionnaire_response,df_questions, df_value_set, strategy = 'overwrite'):
    # create a dict to iterate
    dict_questions = df_questions.to_dict('index')
    # Use first part of the id (before DE) as an ID
    # questionnaire.id = list(dict_questions.keys())[0].split(".DE")[0]
    # delete all item in case of overwrite strategy
    
    if strategy == "overwrite" or questionnaire.item or questionnaire_response.item is None:
        questionnaire.item =[]
        questionnaire_response.item = []
    # recreate item if draft 
    ressource = questionnaire
    response = questionnaire_response
    parent = []
    parent_response =[]
    for id, question in dict_questions.items():
        existing_item = next((ressource.item.pop(index) for index in range(len(ressource.item)) if ressource.item[index].linkId == id), None)
        existing_item_response = next((response.item.pop(index) for index in range(len(response.item)) if response.item[index].linkId == id), None)
        # manage group
        type, detail_1, detail_2 = get_type_details(question)
        if type is None:
            print("${0} is not a valid type, see question ${1}".format(question['type'], id))       
        elif type == "skipped":
            pass
        elif type == "group" and detail_1 == "start":
            item, item_response = add_questionnaire_item_line(existing_item, id, question, df_value_set, strategy)
            item_response, item_response = add_questionnaire_response_item_line(existing_item, id, question, df_value_set, strategy)
            if item is not None:
                # we save the the questionnaire 
                parent.append(ressource)
                parent_response.append(ressource)
                # we save the question as a new ressouce
                ressource = item
                response = item 
                if ressource.item is None:
                    ressource.item =[]
        elif type == "group" and detail_1 == "end":
            if len(parent) == 0:
                print("Question ${0} end of a group that was never opened,  group::end ignored".format( id))
            else:
                # we load the the group question
                temp_ressource = parent.pop()
                temp_ressource_response = parent_response.pop()
                temp_ressource.item.append(ressource)
                temp_ressource_response.item.append(response)
                ressource = temp_ressource
                response = temp_ressource_response

        else:
            item = add_questionnaire_item_line(existing_item, id, question, df_value_set, strategy)
            item_response = add_questionnaire_response_item_line(existing_item, id, question, df_value_set, strategy)
            if item is not None:
                ressource.item.append(item)
                response.item.append(item_response)
    # close all open groups
    while len(parent) > 0:
        temp_ressource = parent.pop()
        temp_ressource_response = parent_response.pop()
        print("group id ${0} is not close and the tool reached the end of the quesitonnaire, closing the group".format( ressource.id))
        temp_ressource.item.append(ressource)
        ressource = temp_ressource
        temp_ressource_response.item.append(response)
        response = temp_ressource_response
    return ressource, response

def add_questionnaire_item_line(existing_item, id, question, df_value_set, strategy):
    # pop the item if it exists
    
    # create or update the item based on the strategy
    if existing_item is None\
    or strategy in ( "overwriteDraft", "overwriteDraftAddOnly" ) and\
        (existing_item.design_note is not None and "status::draft"  in existing_item.design_note):
        new_question = process_quesitonnaire_line(id, question, df_value_set,  existing_item )
        if new_question is not None:
            return new_question
    elif existing_item is not None:
        #put back the item if no update
        return existing_item
    return None

def add_questionnaire_response_item_line(existing_item, id, question, df_value_set, strategy):
    # pop the item if it exists
    
    # create or update the item based on the strategy
    if existing_item is None\
    or strategy in ( "overwriteDraft", "overwriteDraftAddOnly" ):
        new_question = process_quesitonnaire_response_line(id, question, df_value_set,  existing_item )
        if new_question is not None:
            return new_question
    elif existing_item is not None:
        #put back the item if no update
        return existing_item
    return None

def process_quesitonnaire_line(id, question, df_value_set,  existing_item):
    type = get_question_fhir_type(question)
    if pd.notna(question['required']):
        if int(question['required']) == 1:
            question['required']=1
        else : question['required']=0
    else : question['required']=0

    new_question = QuestionnaireItemSDC(
                linkId = id,
                type = type,
                required= question['required'],
                extension = get_question_extension(question, df_value_set ),
                answerValueSet = get_question_valueset(question, df_value_set),
                design_note = "status::draft",
                definition = get_question_definition(question)
            )
    if pd.notna(question['description']):
        new_question.text = question['description']
    
    return new_question

def process_quesitonnaire_response_line(id, question, df_value_set,  existing_item):
    type = get_question_fhir_type(question)
    new_questionResponse = QuestionnaireResponseItemSDC(
                linkId = id,
                extension = get_question_extension(question, df_value_set ),
                definition = get_question_definition(question)
            )
    if pd.notna(question['description']):
        new_questionResponse.text = question['description']
    
    return new_questionResponse
def get_question_fhir_type(question):
    # maps the pyfhirsdc type to real fhir type
    # mapping type are not in questionnaire
    fhir_type = None
    if pd.notna(question['type']):
        type_arr = question['type'].split(" ")
        fhir_type = type_arr[0]
    if fhir_type == 'phone':
        fhir_type = 'string'
    elif fhir_type == 'mapping':
        fhir_type = 'reference'
    elif fhir_type in ("select_one", "select_multiple"):
        fhir_type = "choice"
    elif fhir_type == "checkbox":
        fhir_type = "boolean"
    elif fhir_type == "number":
        fhir_type = "integer"
    return fhir_type
## maps the type of the question e.g. checkbox, to its respective data
## type that FHIR understands e.g. boolean
def get_question_fhir_data_type(question_type):
    switcher_data_types = {
                "checkbox" : "boolean",
                "phone" : "string",
                "text" : "string",
                "mapping" : "Reference", 
                "boolean" : "boolean",
                "date" : "date",
                "time" : "time",
                "dateTime" : "datetime",
                "decimal" :"decimal",
                "CodeableConcept": "CodeableConcept",
                "Reference" : "Reference"
            }
    return switcher_data_types.get(question_type)


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
    if "enableWhenExpression" in question and pd.notna(question["enableWhenExpression"]):
        extensions.append(get_enable_when_expression_ext(question["enableWhenExpression"]))
    if "calculatedExpression" in question and pd.notna(question["calculatedExpression"]):
        extensions.append(get_calculated_expression_ext(question["calculatedExpression"]))
    if "initialExpression" in question and pd.notna(question["initialExpression"]):
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
    if  question['display'] is not None and pd.notna(question['definition']):
        if str(question['definition']).lower() == get_processor_cfg().scope.lower():
            return get_custom_codesystem_url()
        elif len(str(question['definition']))>5:  
            return str(question['definition']).lower()
        else:
            return None
    else:
        return None

def get_type_details(question):
    # structure main_type detail_1::detail_2
    if 'type' not in question or not isinstance(question['type'], str):
        return None, None, None
    type_arr = str(question['type']).split(" ")
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
        questionnaire.id=clean_name(id)
        questionnaire.title=id
        questionnaire.url=get_resource_url('Questionnaire',id) 

    return questionnaire

def init_questionnaire_response(questionnaire):


    #TODO should we have a reference to the subject here with mapping language?
    #TODO same for encounter, source and author
    #questionnaire_response_json.subject = ""
    questionnaire_response = QuestionnaireResponseSDC(
        resourceType = "QuestionnaireResponse",
        id = questionnaire.id,
        #url = get_resource_url('QuestionnaireResponse',questionnaire.id),there is no quesionnaire response urlMust be profile
        questionnaire = questionnaire.url, 
        status = "completed"
    )  
    return questionnaire_response