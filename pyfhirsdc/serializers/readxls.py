from .utils import *
import os
import pandas as pd
import re

def process_data_dicitonnary_table_sheet(conf):
    # Read the config file
    config = read_config_file(conf)
    if config is None:
        exit()
    # ensure the output directoy exist
    if config.processor.outputDirectory is None:
        config.processor.outputDirectory = "./output"
    # check that there is worksheet defined
    if not os.path.exists(config.processor.outputDirectory):
        os.makedirs(config.processor.outputDirectory)
    if not os.path.exists(config.processor.inputFile):
        print("inputFile not found")
        exit()
    if config.processor.worksheets is  None:
        print("no worksheet are provided in processor.worksheets")
        exit()
    else:
        data_elements = []
        for worksheet in config.processor.worksheets:
            #read the dataelement
            worksheet_data_elements = read_excel_worksheet(config.processor, worksheet)
            if worksheet_data_elements is not None:
                data_elements.append(worksheet_data_elements)
        
        # generate extension

        # generate profiles

        # generate the CodeSystem

        # generate the valueSet

        # generate conceptMap

        # generate the questionnaire

        # generate the DE CQL 

        # generate the Concept CQL 

def read_excel_worksheet(config, worksheet):
    df = pd.read_excel(config.inputFile, sheet_name=worksheet, skiprows=config.skiprows)
    if (config.skipcols == 1):
        df.drop(df.columns[[0]], axis=1, inplace=True)
    elif (config.skipcols > 1 ):
        df.drop(df.columns[[0,config.skipcols-1]], axis=1, inplace = True)
    # put the first row a loer character and remove all text between [] and trim and replace other space with _
    #df.iloc[0] = df.iloc[0].str.lower().map(lambda x: re.sub(" ", "_",re.sub(r"\[[^\]+]\]",'',x).strip()))

    # set the column label equal to the fist row
    df = df.rename(columns=lambda s: clean_title(s))

    # we will take only the row with value in "Data Element ID"
    df = df.dropna(axis=0, subset=['data_element_id'])
    
    print(df.columns)
    if len(df.index) > 0:
        return df.values.tolist()
    else:
        return None

def clean_title(str):
    tmp = re.sub(r'(\[\w+\])|(\([^\)]+\))','',str.lower())
    tmp2 = re.sub(r'( +)|(\\ *)|(: *)|(\n *)|(/ *)|(\. *)','_',tmp.strip())
    tmp3 = re.sub(r'(_+)|(_*-_*)','_',tmp2.strip())
    return tmp3
