import os
import re

import pandas as pd

from pyfhirsdc.config import *
from pyfhirsdc.serializers.inputFile import parse_sheets, read_input_file, parse_excel_sheets
from pyfhirsdc.services.generateActivities import generate_activities
from pyfhirsdc.services.generateCodeSystem import generate_custom_code_system
from pyfhirsdc.services.generateLibraries import generate_libraries
from pyfhirsdc.services.generateValueSet import generate_value_sets

from .generatePlanDefinitions import generate_plandefinitions
from .generateProfiles import generate_profiles
from .generateQuestionnaires import generate_questionnaires
from .generateChanges import generateChagnes
from .generateDataDictionary import generate_data_dictionary_page
from .excelToJson import excel_to_json


def process_input_file(conf):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        input_file = read_input_file(get_processor_cfg().inputFile)
        if input_file is not None:
            parse_sheets(input_file, get_processor_cfg().excudedWorksheets)        
            input_file_sheets = parse_excel_sheets(input_file, get_processor_cfg().excudedWorksheets)        

            # generate the CodeSystem
            generate_custom_code_system()  
            # generate questionnaire
            generate_questionnaires()
            # generate libraries
            generate_libraries()
            # generate the valueSet
            generate_value_sets()
            # generate profiles
            generate_profiles()

            # generate conceptMap

            # generate the DE CQL 

            # generate the Concept CQL 

            # generate planDefinition
            generate_plandefinitions()

            # generate Activity
            generate_activities()
            # generate carePlan

            # generate changes
            generateChagnes() 
            # Bundle https://github.com/jkiddo/ember
            # Generate the l2 excel file in json
            excel_to_json(input_file_sheets, input_file)

def process_data_dictionary_file(conf = None):
    data_dictionary_file = read_input_file(get_processor_cfg().data_dictionary_file)
    # Generate the data dictionary page using the data dictionary excel file of the dak
    data_dictionary_worksheets = parse_excel_sheets(data_dictionary_file, get_processor_cfg().data_dictionary_exclude_workSheets)
    generate_data_dictionary_page(data_dictionary_worksheets, data_dictionary_file)
