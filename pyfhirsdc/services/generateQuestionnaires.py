"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""

from pyfhirsdc.converters.questionnaireConverter import generate_questionnaire

from pyfhirsdc.config import get_dict_df

def generate_questionnaires():
    dfs_questionnaire = get_dict_df()['questionnaires']

    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions)






