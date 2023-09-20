
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


import json
import logging
import re

import numpy
import pandas as pd
import textile
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.questionnaire import (QuestionnaireItemAnswerOption,
                                          QuestionnaireItemInitial)
from fhirpathpy import evaluate

from pyfhirsdc.config import get_dict_df, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import (
    get_calculated_expression_ext, get_candidate_expression_ext,
    get_checkbox_ext, get_choice_column_ext, get_constraint_exp_ext,
    get_dropdown_ext, get_enable_when_expression_ext, get_hidden_ext,
    get_horizontal_ext, get_initial_expression_identifier_ext,
    get_instruction_ext, get_item_media_ext, get_number_only_ext,
    get_open_choice_ext, get_popup_ext, get_radio_ext, get_regex_ext,
    get_rendering_style_ext, get_slider_ext, get_subquestionnaire_ext,
    get_toggle_ext, get_unit_ext, get_variable_extension, get_background_color_style_ext)
from pyfhirsdc.converters.utils import (get_custom_codesystem_url, get_media,
                                        get_resource_url,get_type_details,QUESTION_TYPE_MAPPING)
from pyfhirsdc.converters.valueSetConverter import (
    get_condition_valueset_df, get_value_set_answer_options, get_valueset_df)
from pyfhirsdc.models.questionnaireSDC import (QuestionnaireItemSDC,
                                               QuestionnaireSDC)

logger = logging.getLogger("default")
 


def get_timestamp_item():
    return QuestionnaireItemSDC(
                linkId = 'timestamp',
                type = 'dateTime',
                required= False,
                extension = [get_calculated_expression_ext("now()",None), get_hidden_ext()],
                #design_note = "status::draft"            
                )


def get_question_answeroption(question, id, df_questions):
    type, detail_1, detail_2 = get_type_details(question)
    display= get_display(question)
    if type == 'select_boolean':
        return [QuestionnaireItemAnswerOption(valueCoding = Coding(code = id, display = question['label']))]
    elif type.startswith('select_') and 'candidateexpression' not in display :
        options = None
        if type == 'select_condition':
            options = get_value_set_answer_options(get_condition_valueset_df(df_questions))
        elif detail_2 is None  and  get_processor_cfg().answerValueSet != True and   "select_" in type and 'candidateexpression' not in display:
            # we assume it use a local valueset, TODO check if there is actual value in df_value_set
            options = get_value_set_answer_options(get_valueset_df(detail_1, True))
        if options is not None:
            return options
        else:
            logger.error("local ValueSet {0} not defiend in the valueset tab".format(detail_1))
            return None

def get_question_repeats(question):
    return True if question['type'] == 'select_boolean' or question['type'].startswith('select_multiple') or question['type'].startswith('select_condition') else False

def get_clean_html(txt):
    if pd.isna(txt) or txt is None or len(txt)==0:
        return None
    html = textile.textile(txt)
    if html.startswith('\t'):
        html = html[1:]
    if html.startswith('<p>') and len(re.findall(r"</p>", html))==1:
        html = html[3:-4]
    return html
    


    
def get_disabled_display(question):
    display_array = get_display(question)  
    if "readonly" in display_array or "protected" in display_array:
        return True

def get_initial_value(question): #TODO remove when uuid will be supported in cal/fhirpath
    if "initialExpression" in question and pd.notna(question["initialExpression"]):
        if str(question["initialExpression"]).strip() == "uuid()":
            return [QuestionnaireItemInitial(
                valueString = "uuid()"
            )]





## maps the type of the question e.g. checkbox, to its respective data
## type that FHIR understands e.g. boolean
def get_question_fhir_data_type(question_type):
    if pd.notna(question_type) and question_type is not None:
        type_arr = question_type.split(" ")
        fhir_type = type_arr[0]
        
        return QUESTION_TYPE_MAPPING.get(fhir_type.lower())

def get_unit(display):
    regex_unit = re.compile("^unit::.*")
    unit = list(filter(regex_unit.match, display)) 
    if unit is not None and len(unit) == 1:
        unit_part = unit[0].split('::')
        if len(unit_part) == 2:
            return unit_part[1]
    

def get_question_extension(question, question_id, df_questions = None ):
    
    extensions = []
    display= get_display(question)
    unit = get_unit(display)
    regex_slider = re.compile("^slider::.*")
    slider = list(filter(regex_slider.match, display))
    type, detail_1, detail_2 = get_type_details(question)

    style_str = get_style(display)
    if style_str is not None and len(style_str)>0:
        extensions.append(get_rendering_style_ext(style_str))
        
    if type == 'phone':
        extensions.append(get_regex_ext('^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$'))
        extensions.append(get_number_only_ext())
    color_str = get_bk_color(display)
    if color_str is not None and len(color_str)>0:
        extensions.append(get_background_color_style_ext(color_str))
        
    if 'item-popup' in display:
        extensions.append(get_popup_ext())
    if type == 'boolean' or 'horizontal' in display and 'hidden' not in display :
        extensions.append(get_horizontal_ext())
    if "constraintExpression" in question and pd.notna(question["constraintExpression"]) and question["constraintExpression"] !='':
        message =  question["constraintDescription"] if "constraintDescription" in question and pd.notna(question["constraintDescription"]) else "Validation error"
        exts = get_constraint_exp_ext(question_id,question["constraintExpression"],message, df_questions)
        if exts is not None and len(exts)>0:
            extensions += exts
    # TODO support other display than drop down
    if (type.lower() == 'select_boolean'):
        extensions.append(get_checkbox_ext())
    elif type == "questionnaire":
        extensions.append(get_subquestionnaire_ext(question["id"]))
    elif "select_" in type and "dropdown"  in display :
        extensions.append(get_dropdown_ext())
    elif type == "select_multiple":
        # only way to have select multiple repeat = true is not enough
        if "open"  in display :
            extensions.append(get_open_choice_ext())
        if "checkbox" in display or "radio" in display:
            extensions.append(get_checkbox_ext())
    elif type == "select_one":
        if "checkbox" in display or "radio" in display:
            extensions.append(get_radio_ext())
    if "select_" in type and type.lower() != 'select_boolean' and 'readonly' not in display and 'hidden' not in display:
        for value in display:
            if value.strip().startswith('toggle'):
                elms = value.split('::')
                if len(elms)==3:
                    extensions.append(get_toggle_ext(elms[1], elms[2], df_questions))

    if type.lower() in ('decimal','integer','number','quantity') and unit is not None:
        extensions.append(get_unit_ext(unit))
    if type.lower() in ('decimal','integer','number') and len(slider) == 1 :
        extensions = extensions+(get_slider_ext(slider[0], question["label"]))
    if "select_" in type and   "candidateexpression"  in display:
        extensions = get_question_choice_column(extensions, detail_1)
    if "hidden"  in display:
        extensions.append(get_hidden_ext())
    elif "instruction" in display  and type in ["display","note"]:
        extensions.append(get_instruction_ext())

    if "media" in question and pd.notna(question["media"]) and question["media"] !='' and\
        True: # media in help ('help' not in question or pd.isna(question['help'])):
        type_media, url_media = get_media(question)
        if type_media is not None:
            extensions.append(get_item_media_ext(type_media, url_media))

    if "enableWhenExpression" in question and pd.notna(question["enableWhenExpression"]) and question["enableWhenExpression"] !='':
        extensions.append(get_enable_when_expression_ext(question["enableWhenExpression"],df_questions))    
    if "calculatedExpression" in question and pd.notna(question["calculatedExpression"]) and question["calculatedExpression"] !='':
        extensions.append(get_calculated_expression_ext(question["calculatedExpression"],df_questions))
    if "initialExpression" in question and pd.notna(question["initialExpression"]) and question["initialExpression"] !='':
        if not str(question["initialExpression"]).strip() == "uuid()": #TODO remove when uuid will be supported
            extensions.append(get_initial_expression_identifier_ext(question_id))
    if 'parentId' in  df_questions:
        df_variables = df_questions[(df_questions.parentId==id) & (df_questions.type=='variable')].dropna(axis=0, subset=['calculatedExpression'])
        for index, var in df_variables.iterrows():
            extensions.append(get_variable_extension(var['id'], var['calculatedExpression'],df_questions))
    return extensions

def get_display(question):
    display_str = str(question["display"]) if "display" in question and pd.notna(question["display"]) else None
    if display_str is not None:
        return display_str.split('||')
    else:
        return []

def get_style(display_arr):
    for display_str in display_arr:
        display_elmts = display_str.split('::')
        if display_elmts[0] == 'style' and len(display_elmts) == 2:
            return display_elmts[1]
        
def get_bk_color(display_arr):
    for display_str in display_arr:
        display_elmts = display_str.split('::')
        if display_elmts[0] == 'background-color' and len(display_elmts) == 2:
            return display_elmts[1]   
    


def get_question_valueset(question):
    # split question type and details
    display= get_display(question)
    type, detail_1, detail_2 = get_type_details(question)
    # split each deatil
    if "select_" in type and 'candidateexpression' not in display and type != 'select_boolean':
        if detail_1 == "url":
            return  (detail_2)
        elif detail_2 is None  and  get_processor_cfg().answerValueSet == True:
            df_value_set = get_dict_df()['valueset']
            # we assume it use a local valueset, TODO check if there is actual value in df_value_setx
            valueset_dict = df_value_set[df_value_set['valueSet'] == detail_1]['valueSet'].unique()
            if isinstance(valueset_dict, numpy.ndarray) and len(valueset_dict)>0:
                return  get_resource_url("ValueSet", detail_1)
            else:
                logger.error("local ValueSet {0} not defiend in the valueset tab".format(detail_1))
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




def validate_fhirpath(resource, elm = None, elm_root = "%resource"):
    if elm == None:
        elm = resource
    # go through extension
    if hasattr(elm, "extension") and elm.extension is not None:
        for ext in elm.extension:
            if hasattr(ext, "valueExpression") and ext.valueExpression is not None and ext.valueExpression.language =="text/fhirpath":
                expr = ext.valueExpression.expression
                expr= expr.replace('%this', elm_root)
                js_res = json.loads(resource.json())
                evaluate( expr)
            validate_fhirpath(resource, ext, elm_root)
        if hasattr(elm, "item") and elm.item is not None:
            for item in  elm.item:
                elm_root_child = elm_root + ".item.where(linkid='{}')".format(item.linkId)
                validate_fhirpath(resource, item, elm_root_child)
                
