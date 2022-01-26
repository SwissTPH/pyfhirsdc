from pyfhirsdc.serializers.inputFile import read_input_file, parse_sheets
from pyfhirsdc.serializers.json import read_json
from pyfhirsdc.config import *
from .generateExtensions import generate_extensions
from .generateQuestionnaires import generate_questionnaires
import os
import pandas as pd
import re



def process_input_file(conf):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        input_file = read_input_file(get_processor_cfg().inputFile)
        if input_file is not None:
            questionnaires, decision_tables,\
                value_set, care_plan, settings,\
                choice_column, cql = parse_sheets(input_file, get_processor_cfg().excudedWorksheets)        
            # generate questionnaire
            generate_questionnaires(questionnaires)

            # generate profiles

            # generate the CodeSystem

            # generate the valueSet

            # generate conceptMap

            # generate the DE CQL 

            # generate the Concept CQL 

            # generate planDefinition


            # generate carePlane


