
import pandas as pd
import re

def clean_str(str):
    tmp = re.sub(r'(\[\w+\])|(\([^\)]+\))','',str.lower())
    tmp2 = re.sub(r'( +)|(\\ *)|(: *)|(\n *)|(/ *)|(\. *)','_',tmp.strip())
    tmp3 = re.sub(r'(_+)|(_*-_*)','_',tmp2.strip())
    return tmp3


def read_input_file(config):
    try:
        file = pd.ExcelFile(config.inputFile)
    except Exception as e:
        print("Error while opening the from the file %s",config.inputFile )
        return None
    return file

def parse_sheets(inputFile, excudedWorksheets):
    sheets = inputFile.sheet_names
    questionnaires = []
    decision_tables = []
    value_set = None
    settings = None
    for worksheet in sheets:
        if worksheet not in excudedWorksheets:
            df = inputFile.parse(worksheet)
            if worksheet.startswith('q.'):
                if validate_questionnaire_sheet(df):
                    questionnaires[worksheet[2:]] = df
                else:
                    break
            elif worksheet.startswith('d.'):
                if validate_decision_tables_sheet(df):
                    decision_tables[worksheet[2:]] = df
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
            elif care_plan == "carePlan":
                if validate_value_set_sheet(df):
                    care_plan = df
                else:
                    break
            elif worksheet == "cql":
                if validate_value_set_sheet(df):
                    cql = df
                else:
                    break
    return questionnaires, decision_tables, value_set, care_plan, settings, choice_column, cql

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