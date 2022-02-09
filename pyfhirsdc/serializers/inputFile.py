
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
        print("Error while opening the from the file %s",input_file_path )
        return None
    return file

def parse_sheets(input_file, excudedWorksheets):
    sheets = input_file.sheet_names
    questionnaires = {}
    decision_tables = {}
    value_set = None
    for worksheet in sheets:
        print ("loading sheet %{0}".format( worksheet))
        if excudedWorksheets is None or worksheet not in excudedWorksheets:
            df = input_file.parse(worksheet)
            if worksheet.startswith('q.'):
                if validate_questionnaire_sheet(df):
                    questionnaires[worksheet[2:]] = df
                else:
                    break
            elif worksheet.startswith('pd.'):
                if validate_decision_tables_sheet(df):
                    decision_tables[worksheet[3:]] = df
                else:
                    break
            elif worksheet == "valueSet":
                if validate_value_set_sheet(df):
                    value_set = df
                else:
                    break
            elif worksheet == "choiceColumn":
                if validate_value_set_sheet(df):
                    choice_column = df
                else:
                    break
            elif worksheet == "carePlan":
                if validate_value_set_sheet(df):
                    care_plan = df
                else:
                    break
            elif worksheet == "cql":
                if validate_value_set_sheet(df):
                    cql = df
                else:
                    break
    return questionnaires, decision_tables, value_set, care_plan, choice_column, cql

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