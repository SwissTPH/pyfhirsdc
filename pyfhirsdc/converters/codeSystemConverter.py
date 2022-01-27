"""
 convert dataframe to to fhir coding system concept

"""
from fhir.resources.codesystem import CodeSystemConcept

def generate_questionnaire_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions.dropna(axis=0, subset=['id']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        concept.append(
            CodeSystemConcept(
                definition = question["description"],
                code = id,
                display =  question["label"]
            )
        )
    return concept


def generate_valueset_concept(df_value_set):
    concept = []
    # remove the line without id
    value_set = df_value_set.dropna(axis=0, subset=['id']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in value_set.items():
        concept.append(
            CodeSystemConcept(
                definition = question["description"],
                code = id,
                display =  question["label"]
            )
        )
    return concept
