"""
    Service to generate the questionnaires ressources
    needs the sheet:
        - q.X
        - choiceColumn
        - valueSet
"""

from pyfhirsdc.converters.questionnaireConverter import generate_questionnaire

from pyfhirsdc.config import get_dict_df

from pyfhirsdc.serializers.docSerializer import  write_docs

def generate_questionnaires():
    dfs_questionnaire = get_dict_df()['questionnaires']
    doc_buffer = ""
    for name, questions in dfs_questionnaire.items():
        generate_questionnaire(name ,questions)
        doc_buffer += "{{% include Activity{}.md %}}\n\n".format(name.capitalize())
    write_docs(doc_buffer,"AllActivities")

    
    



