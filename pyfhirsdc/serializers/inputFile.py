
import pandas as pd

import re

def clean_str(str):
    tmp = re.sub(r'(\[\w+\])|(\([^\)]+\))','',str.lower())
    tmp2 = re.sub(r'( +)|(\\ *)|(: *)|(\n *)|(/ *)|(\. *)','_',tmp.strip())
    tmp3 = re.sub(r'(_+)|(_*-_*)','_',tmp2.strip())
    return tmp3


def read_input_file(input_file_path):
    try:
        file = pd.ExcelFile(input_file_path)
    except Exception as e:
        print("Error while opening the from the file {0} with error {1}".format(input_file_path, e) )
        return None
    return file


def read_tsv_file(input_file_path):
    try:
        file = pd.read_csv(input_file_path, sep='\t')
    except Exception as e:
        print("Error while opening the from the file {0} with error {1}".format(input_file_path, e) )
        return None
    return file

def parse_sheets(input_file, excudedWorksheets):
    sheets = input_file.sheet_names
    dfs_questionnaire = {}
    dfs_decision_table = {}
    value_set = None
    for worksheet in sheets:
        print ("loading sheet {0}".format( worksheet))
        if excudedWorksheets is None or worksheet not in excudedWorksheets:
            df = input_file.parse(worksheet)
            # strip space
            df = df.applymap(lambda x: x.strip() if type(x)==str else x)
            if worksheet.startswith('q.'):
                if validate_questionnaire_sheet(df):
                    dfs_questionnaire[worksheet[2:]] = df
                else:
                    break
            elif worksheet.startswith('pd.'):
                if validate_decision_tables_sheet(df):
                    dfs_decision_table[worksheet[3:]] = df
                else:
                    break
            elif worksheet == "valueSet":
                if validate_value_set_sheet(df):
                    value_set = df
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
            elif worksheet == "carePlan":
                if validate_value_set_sheet(df):
                    df_care_plan = df
                else:
                    break
            elif worksheet == "cql":
                if validate_value_set_sheet(df):
                    df_cql = df
                else:
                    break
    return dfs_questionnaire, dfs_decision_table, value_set, df_care_plan, df_profile, df_extension, df_cql

def validate_questionnaire_sheet(df):
    return True

def validate_decision_tables_sheet(df):
    return True

def validate_choice_column_sheet(df):
    return True

def validate_value_set_sheet(df):
    return True


def validate_care_plan_sheet(df):
    return True

def validate_cql_sheet(df):
    return True