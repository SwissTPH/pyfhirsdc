
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


import numpy
from pandas import DataFrame
from pyfhirsdc.models.questionnaireSDC import QuestionnaireItemSDC
from fhir.resources.fhirtypes import Canonical
from pyfhirsdc.models.extensions import get_dropdown_ext, get_candidate_expression_ext, get_choice_column_ext
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg

def convert_df_to_questionitems(questionnaire, df_questions, df_value_set, df_choiceColumn, strategy = 'overwrite'):
    dict_questions = df_questions.to_dict('index')
    if questionnaire.item is None or strategy == "overwrite":
        questionnaire.item =[]

    for id, question in dict_questions.items():
        # pop the item if it exists
        existing_item = next((questionnaire.item.pop(index) for index in range(len(questionnaire.item)) if questionnaire.item[index].linkId == id), None)
        # create or update the item based on the strategy
        if existing_item is None\
        or strategy in ( "overwriteDraft", "overwriteDraftAddOnly" ) and\
            (existing_item.design_note is not None and "status::draft"  in existing_item.design_note):
            new_question = process_quesitonnaire_line(id, question, df_value_set, df_choiceColumn, existing_item )
            if new_question is not None:
                questionnaire.item.append(new_question)
        elif existing_item is not None:
            #put back the item if no update
            questionnaire.item.append(existing_item)
    return questionnaire

def process_quesitonnaire_line(id, question, df_value_set, df_choiceColumn, existing_item):
    new_question = None
    extensions = []

    type = get_question_type(question)

    if type is None:
        print(question['type'], " is not a valid type, see question ", id)
        return None        
    elif type == "skipped":
        return None
    # merge extensions

    #TODO manage code with custom coding system
    #TODO manage choicecolumn
    new_question = QuestionnaireItemSDC(
            linkId = id,
            type = type,
            extension = get_question_extension(question, df_choiceColumn ),
            answerValueSet = get_question_valueset(question, df_value_set),
            design_note = "status::draft",
            text = question['description'],
            definition = get_question_definition(question)
        )
    
    return new_question

def get_question_type(question):
    # mapping type are not
    fhir_type = None
    type_arr = question['type'].split(" ")
    fhir_type = type_arr[0]
    if fhir_type in ("select_one", "select_multiple"):
        fhir_type = "choice"
    elif fhir_type == "checkbox":
        fhir_type = "boolean"
    elif fhir_type == "checkbox":
        fhir_type = "boolean"
    return fhir_type

def get_question_extension(question, df_choiceColumn ):
    extensions = []
    type, detail_1, detail_2 = get_type_details(question)
    # TODO support other display than drop down
    if "select_" in type and question["display"] == "dropdown" :
        extensions.append(get_dropdown_ext())
    if "select_" in type and\
        detail_2 and detail_1 == "candidateExpression"\
            and len(question["display"])>1:
        extensions.append(get_candidate_expression_ext(question["description"], detail_2))
        extensions = get_question_choice_column(extensions, question["display"], df_choiceColumn)

    return extensions



def get_question_valueset(question, df_value_set):
    # split question type and details
    type, detail_1, detail_2 = get_type_details(question)
    # split each deatil
    if "select_" in type:
        if detail_1 == "url":
            return  (detail_2)
        else :
            # we assume it use a local valueset, TODO check if there is actual value in df_value_set
            return (get_fhir_cfg().canonicalBase + "valueset/valueset-"+detail_1)
    else:
        return None

def get_question_choice_column(extensions, candidate_expression, df_choiceColumn):
    #TODO check choiceColumn if there is any candidate_expression matching
    # filter DF choice column
    
    choice_columns = df_choiceColumn[df_choiceColumn['candidate_expression'] == candidate_expression].set_index('label').to_dict('index')
    for label, choice_column in choice_columns.items():
        extension = get_choice_column_ext(choice_column["path"],
            label,choice_column["width"],choice_column["forDisplay"])
        if extension is not None:
            extensions.append(extension)

    return extensions

    



    pass

def get_question_definition(question):
    if  question['definition'] is not None and question['definition'] is not numpy.nan:
        if question['definition'].lower() == get_processor_cfg().scope.lower():
            return (get_fhir_cfg().canonicalBase + "codingsystem/codesystem-"+ get_processor_cfg().scope.lower() + "-custom-codes-codes.json")
        elif len(question['definition'])>5:  
            return question['definition'].lower()
        else:
            return None
    else:
        return None

def get_type_details(question):
    type_arr = question['type'].split(" ")
    # split each deatil
    if len(type_arr)>1:
        detail_arr = type_arr[1].split('::')
        if len(detail_arr)>1:
            return type_arr[0], detail_arr[0], detail_arr[1]
        else:
            return type_arr[0], detail_arr[0], None
    else:
        return type_arr[0], None, None

