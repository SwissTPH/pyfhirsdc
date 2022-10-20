
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


import json
import re

import numpy
import pandas as pd
from fhir.resources.coding import Coding
from fhir.resources.questionnaire import (QuestionnaireItemAnswerOption,
                                          QuestionnaireItemInitial)

from pyfhirsdc.config import get_defaut_fhir, get_dict_df, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import (
    get_calculated_expression_ext, get_candidate_expression_ext,
    get_checkbox_ext, get_choice_column_ext, get_constraint_exp_ext,
    get_dropdown_ext, get_enable_when_expression_ext, get_hidden_ext,
    get_initial_expression_identifier_ext, get_open_choice_ext, get_slider_ext,
    get_unit_ext, get_variable_extension)
from pyfhirsdc.converters.utils import (clean_name, get_custom_codesystem_url,
                                        get_resource_url)
from pyfhirsdc.models.questionnaireSDC import (QuestionnaireItemSDC,
                                               QuestionnaireSDC)


def convert_df_to_questionitems(ressource,df_questions, parentId = None, strategy = 'overwrite'):
    # create a dict to iterate
    if parentId is None:
        if 'parentId' in df_questions:
            dict_questions = df_questions[df_questions.parentId.isna()].to_dict('index')
        else:
            dict_questions = df_questions.to_dict('index')
    else:
        if 'parentId' in df_questions:
            dict_questions = df_questions[df_questions.parentId == parentId ].to_dict('index')
        else:
            return ressource
    # Use first part of the id (before DE) as an ID
    # questionnaire.id = list(dict_questions.keys())[0].split(".DE")[0]
    # delete all item in case of overwrite strategy
    
    if strategy == "overwrite" or ressource.item :
        ressource.item =[]
    if ressource.item is None:
       ressource.item =[]
    # recreate item if draft 
    ressource = ressource

    # add timestamp
    ressource.item.append(get_timestamp_item())
    for id, question in dict_questions.items():
        existing_item = next((ressource.item.pop(index) for index in range(len(ressource.item)) if ressource.item[index].linkId == id), None)
        # manage group
        type, detail_1, detail_2 = get_type_details(question)
        if type is None:
            print("${0} is not a valid type, see question ${1}".format(question['type'], id))       
        elif type == "skipped":
            pass
        elif  type == 'variable':
            variable = get_variable_extension(id,question['calculatedExpression'])
            if variable is not None:
                ressource.extension.append(variable)
        
        elif type == "group" :
            item = add_questionnaire_item_line(df_questions, existing_item, id, question,  strategy)
            if item is not None:
                # we save the the questionnaire 
                convert_df_to_questionitems(item,df_questions, id ,strategy = 'overwrite')
                # we save the question as a new ressouce
  
                ressource.item.append(item)

        else:
            item = add_questionnaire_item_line(df_questions, existing_item, id, question,  strategy)
            if item is not None:
                ressource.item.append(item)
    # close all open groups


    return ressource

def get_timestamp_item():
    return QuestionnaireItemSDC(
                linkId = 'timestamp',
                type = 'dateTime',
                required= False,
                extension = [get_calculated_expression_ext("now()"), get_hidden_ext()],
                #design_note = "status::draft"            
                )

def add_questionnaire_item_line(df_questions, existing_item, id, question,  strategy):
    # pop the item if it exists
    
    # create or update the item based on the strategy
    if existing_item is None\
    or strategy in ( "overwriteDraft", "overwriteDraftAddOnly" ) and\
        (existing_item.design_note is not None and "status::draft"  in existing_item.design_note):
        new_question = process_quesitonnaire_line(id, question,df_questions,   existing_item )
        if new_question is not None:
            return new_question
    elif existing_item is not None:
        #put back the item if no update
        return existing_item
    return None

def get_question_answeroption(question, id):
    if question["type"] == 'select_boolean':
        return [QuestionnaireItemAnswerOption(valueCoding = Coding(code = id, display = question['label']))]

def get_question_repeats(question):
    return True if question['type'] == 'select_boolean' or question['type'].startswith('select_multiple') else False


def process_quesitonnaire_line(id, question, df_questions,  existing_item):
    type =get_question_fhir_data_type(question['type'])
    if pd.notna(question['required']):
        if int(question['required']) == 1:
            question['required']=1
        else : question['required']=0
    else : question['required']=0
    if 'parentId' in  df_questions:
        df_question = df_questions[df_questions.parentId==id]
    else:
        df_question = None
    if type is not None:
        new_question = QuestionnaireItemSDC(
                    linkId = id,
                    type = type,
                    required= question['required'],
                    extension = get_question_extension(question, id, df_question),
                    answerValueSet = get_question_valueset(question),
                    answerOption=get_question_answeroption(question, id),
                    repeats= get_question_repeats(question),
                    design_note = "status::draft",
                    definition = get_question_definition(question),
                    initial = get_initial_uuid(question)
                )
        if pd.notna(question['label']) and question['type'] != "select_boolean":
            new_question.text = question['label']
        #FIXME DEMO WORKARROUND REQUIRE NOT WORKING WITH SKIP LOGIC
        #for ext in new_question.extension:
        #    if ext.url == 'http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-enableWhenExpression':
        #        new_question.required = False
                        
                    
                
        return new_question

def get_initial_uuid(question): #TODO remove when uuid will be supported in cal/fhirpath
    if "initialExpression" in question and pd.notna(question["initialExpression"]):
        if question["initialExpression"].strip() == "uuid()":
            return [QuestionnaireItemInitial(
                valueString = "uuid()"
            )]

QUESTION_TYPE_MAPPING = {
                'select_one':'choice',
                'select_multiple':'choice',
                'select_boolean': 'choice',
                'mapping': None,
                '{{cql}}':None,
                'variable':None,
                "checkbox" : "boolean",
                "phone" : "integer",
                "text" : "string",
                "boolean" : "boolean",
                "date" : "date",
                "dateTime" : "dateTime",
                "time" : "time",
                "dateTime" : "datetime",
                "decimal" :"decimal",
                "quantity" :"quantity",
                "integer" :"integer",
                "number" :"integer",
                "CodeableConcept": "CodeableConcept",
                "Reference" : "Reference",
                'group':'group'      
}


## maps the type of the question e.g. checkbox, to its respective data
## type that FHIR understands e.g. boolean
def get_question_fhir_data_type(question_type):
    if pd.notna(question_type) and question_type is not None:
        type_arr = question_type.split(" ")
        fhir_type = type_arr[0]
        
        return QUESTION_TYPE_MAPPING.get(fhir_type)


def get_question_extension(question, question_id, df_question = None ):
    
    extensions = []
    display= get_display(question)
    
    regex_unit = re.compile("^unit::.*")
    unit = list(filter(regex_unit.match, display)) 
    regex_slider = re.compile("^slider::.*")
    slider = list(filter(regex_slider.match, display))
    type, detail_1, detail_2 = get_type_details(question)
    if "constraintExpression" in question and pd.notna(question["constraintExpression"])\
        and "constraintDescription" in question and pd.notna(question["constraintDescription"]):
        extensions.append(get_constraint_exp_ext(question_id,question["constraintExpression"],question["constraintDescription"]))
    # TODO support other display than drop down
    if (type.lower() == 'select_boolean'):
        extensions.append(get_checkbox_ext())
    if "select_" in type and "dropdown"  in display :
        extensions.append(get_dropdown_ext())
    elif type == "select_multiple":
        # only way to have select multiple repeat = true is not enough
        extensions.append(get_open_choice_ext())
    if type.lower() in ('decimal','integer','number') and len(unit) == 1 :
        extensions.append(get_unit_ext(unit[0]))
    if type.lower() in ('decimal','integer','number') and len(slider) == 1 :
        extensions = extensions+(get_slider_ext(slider[0], question["label"]))
    if "select_" in type and   "candidateexpression"  in display:
        extensions = get_question_choice_column(extensions, detail_1)
    if "hidden"  in display:
        extensions.append(get_hidden_ext())
    if "enableWhenExpression" in question and pd.notna(question["enableWhenExpression"]):
        extensions.append(get_enable_when_expression_ext(question["enableWhenExpression"]))    
    if "calculatedExpression" in question and pd.notna(question["calculatedExpression"]):
        extensions.append(get_calculated_expression_ext(question["calculatedExpression"]))
    if "initialExpression" in question and pd.notna(question["initialExpression"]):
        if not question["initialExpression"].strip() == "uuid()": #TODO remove when uuid will be supported
            extensions.append(get_initial_expression_identifier_ext(question_id))
    if df_question is not None and len(df_question)>0:
        df_variables = df_question[df_question.type=='variable'].dropna(axis=0, subset=['calculatedExpression'])
        for index, var in df_variables.iterrows():
            extensions.append(get_variable_extension(var['id'], var['calculatedExpression']))
    return extensions

def get_display(question):
    display_str = str(question["display"]).lower() if "display" in question and pd.notna(question["display"]) else None
    if display_str is not None:
        return display_str.split('||')
    else:
        return []


def get_question_valueset(question):
    df_value_set = get_dict_df()['valueset']
    # split question type and details
    display= get_display(question)
    type, detail_1, detail_2 = get_type_details(question)
    # split each deatil
    if "select_" in type and 'candidateexpression' not in display or type == 'select_boolean':
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

def get_question_choice_column(extensions, candidate_expression):
    df_value_set = get_dict_df()['valueset']
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
    display = get_display(question)
    # if definition == scope then build def based on canonical base, if not take the def from the xls if any
    if  question['label'] is not None and pd.notna(question['definition']):
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
    #commented to force re-generation questionnaire_json = read_resource(filepath, "Questionnaire")
    questionnaire_json = None
    default =get_defaut_fhir('Questionnaire')
    if questionnaire_json is not None :
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(questionnaire_json))  
    elif default is not None:
        # create file from default
        questionnaire = QuestionnaireSDC.parse_raw( json.dumps(default))
        questionnaire.id=clean_name(id)
        questionnaire.title=id
        questionnaire.name=id
        questionnaire.url=get_resource_url('Questionnaire',id) 

    return questionnaire
