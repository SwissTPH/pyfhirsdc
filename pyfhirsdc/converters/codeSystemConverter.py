"""
 convert dataframe to to fhir coding system concept

"""
from fhir.resources.codesystem import CodeSystemConcept
from pyfhirsdc.converters.utils import get_custom_codesystem_url

from pyfhirsdc.converters.valueSetConverter import get_value_set_additional_data_keyword

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
    value_set = df_value_set[~df_value_set['code'].isin(
        get_value_set_additional_data_keyword()
        )]
    value_set = value_set.dropna(axis=0, subset=['code']).set_index('code').to_dict('index')
    # remove the line without id
    for code, question in value_set.items():
        concept.append(
            CodeSystemConcept(
                definition = question["definition"],
                code = code,
                display =  question["display"],
            )
        )
    return concept
