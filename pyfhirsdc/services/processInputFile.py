from pyfhirsdc.serializers.inputFile import read_input_file, parse_sheets
from pyfhirsdc.config import *
from pyfhirsdc.services.generateActivities import generate_activities
from pyfhirsdc.services.generateCodeSystem import generate_custom_code_system
from pyfhirsdc.services.generateValueSet import generate_value_sets
from .generateQuestionnaires import generate_questionnaires
from .generatePlanDefinitions import generate_plandefinitions
from .generateProfiles import generate_profiles

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
            dfs_questionnaire, dfs_decision_table, df_value_set, df_profile,\
                 df_extension, df_cql = parse_sheets(input_file, get_processor_cfg().excudedWorksheets)        
            input_file.close()
            print(len(dfs_questionnaire))
            # generate the CodeSystem
            generate_custom_code_system()  
            # generate questionnaire
            generate_questionnaires()


 

            
            # generate the valueSet
            generate_value_sets()
            # generate profiles
            generate_profiles()

            # generate conceptMap

            # generate the DE CQL 

            # generate the Concept CQL 

            # generate planDefinition
            generate_plandefinitions(dfs_decision_table)

            # generate Activity
            generate_activities()
            # generate carePlan

            # Bundle https://github.com/jkiddo/ember



