
# conversion strategy
# overwrite : full overwrite of the file
# overwriteAddonly : don't update, just add new Item/details
# overwriteDraft: overwrite only the question with "status::draft" in items[linkID].designNote
# (not covered yet)overwriteDraftAddOnly : don't update existing item details, just add details if they are not existing in question with "status::draft" in items[linkID].designNote


from pyfhirsdc.models.questionnaireSDC import QuestionnaireItemSDC


def convert_df_to_questionitems(questionnaire, df_questions, strategy = 'overwrite'):
    dict_questions = df_questions.to_dict('index')
    if questionnaire.item is None or strategy == "overwrite":
        questionnaire.item =[]

    for id, question in dict_questions.items():
        # look if the item exists
        existing_item = next((questionnaire.item.pop(index) for index in range(len(questionnaire.item)) if questionnaire.item[index].linkId == id), None)
        # create or update the item based on the strategy
        if existing_item is None\
        or strategy == "overwriteDraft" and\
            (existing_item.design_note is None or "status::draft" not in existing_item.design_note):
            new_question = process_quesitonnaire_line(id, question, existing_item )
            questionnaire.item.append(new_question)
    return questionnaire

def process_quesitonnaire_line(id, question, existing_item):
    new_question = None
    if existing_item is None:
        new_question = QuestionnaireItemSDC(
            linkId = id,
            type = get_question_type(question['type']),
            design_note = "status::draft",
        )
    else:
        new_question = existing_item
        new_question.type = get_question_type(question['type'])
    new_question.design_note = "status::draft"
    
    return new_question

def get_question_type(type):
    #ToDO
    return "boolean"