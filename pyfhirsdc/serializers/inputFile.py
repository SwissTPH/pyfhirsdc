
import logging
import re

import pandas as pd

from pyfhirsdc.config import set_dict_df

logger = logging.getLogger("default")

def clean_str(str):
    tmp = re.sub(r'(\[\w+\])|(\([^\)]+\))','',str.lower())
    tmp2 = re.sub(r'( +)|(\\ *)|(: *)|(\n *)|(/ *)|(\. *)','_',tmp.strip())
    tmp3 = re.sub(r'(_+)|(_*-_*)','_',tmp2.strip())
    return tmp3


def read_input_file(input_file_path):
    try:
        file = pd.ExcelFile(input_file_path)
    except Exception as e:
        logger.error("while opening the from the file {0} with error {1}".format(input_file_path, e) )
        return None
    return file


def parse_excel_sheets(data_dictionary_file, excludedWorksheets):
    worksheets = data_dictionary_file.sheet_names
    filtered_sheets = []
    for worksheet in worksheets:
        logger.info("loading sheet {0}".format(worksheet).replace("\u2265", " "))
        if worksheet.lower() not in excludedWorksheets:
            filtered_sheets.append(worksheet)
    return filtered_sheets

def parse_sheets(input_file, excudedWorksheets):
    worksheets = input_file.sheet_names
    dfs_questionnaire = {}
    dfs_decision_table = {}
    df_value_set = None
    df_profile = None
    df_extension = None
    df_changes = None
    dfs_cql = {}
    for worksheet in worksheets:
        logger.info("loading sheet {0}".format( worksheet))
        if excudedWorksheets is None or worksheet not in excudedWorksheets:
            df = input_file.parse(worksheet)
            worksheet= worksheet.replace("_", ".")
            # strip space
            df = df.dropna(how='all').applymap(lambda x: x.strip() if type(x)==str else x)
            if worksheet.startswith('q.'):
                if validate_questionnaire_sheet(df):
                    dfs_questionnaire[worksheet[2:31]] = df
                else:
                    break
            elif worksheet.startswith('pd.'):
                if validate_decision_tables_sheet(df):
                    dfs_decision_table[worksheet[3:]] = df
                else:
                    break
            elif worksheet == "valueSet":
                if validate_value_set_sheet(df):
                    df_value_set = df
                else:
                    break
            elif worksheet == "profile":
                if validate_value_set_sheet(df):
                    df_profile = df
                else:
                    break
            elif worksheet == "extension":
                if validate_value_set_sheet(df):
                    df_extension = df
                else:
                    break
            elif worksheet.startswith('l.'):
                if validate_cql_sheet(df):
                    dfs_cql[worksheet[2:31]] = df
                else:
                    break
            elif worksheet == "changes":
                if validate_changes_sheet(df):
                    df_changes = df
                else: 
                    break

            elif worksheet.startswith(('q.','l.','c.','r.')):
                df = df.dropna(axis=0,subset=['type'])
                if worksheet.startswith('q.'):
                    if validate_questionnaire_sheet(df):
                        id_from_df = df[df['id']=='{{id}}']
                        name = worksheet[2:31] if len(id_from_df)==0 else id_from_df.iloc[0]['label']
                        dfs_questionnaire[name] = df
                    else:
                        break
                elif worksheet.startswith('c.'):
                    if validate_condition_sheet(df):
                        id_from_df = df[df['id']=='{{id}}']
                        name = worksheet[2:31] if len(id_from_df)==0 else id_from_df.iloc[0]['label']
                        dfs_conditions[name] = df
                    else:
                        break
                elif worksheet.startswith('r.'):
                    if validate_condition_sheet(df):
                        id_from_df = df[df['id']=='{{id}}']
                        name = worksheet[2:31] if len(id_from_df)==0 else id_from_df.iloc[0]['label']
                        dfs_recommendations[name] = df
                    else:
                        break
                elif worksheet.startswith('l.'):
                    if validate_library_sheet(df):
                        id_from_df = df[df['id']=='{{id}}']
                        name = worksheet[2:31] if len(id_from_df)==0 else id_from_df.iloc[0]['label']
                        dfs_cql[worksheet[2:31]] = df
                    else:
                        break
            else:
                logger.warning(f" worksheet {worksheet} not parsed, need to be change, valueset or start with c., l., q., r.")


    set_dict_df({
        "questionnaires" : dfs_questionnaire,
        "decisions_tables" : dfs_decision_table,
        "valueset" : df_value_set,
        "profile" : df_profile,
        "extension" : df_extension,
        "libraries" : dfs_cql,
        "changes": df_changes
    })

def validate_questionnaire_sheet(df):
    return True

def validate_decision_tables_sheet(df):
    return True

def validate_choice_column_sheet(df):
    return True

def validate_value_set_sheet(df):
    return True

def validate_cql_sheet(df):
    return True

def validate_changes_sheet(df): 
    return True