import os
import re

import pandas as pd

from pyfhirsdc.config import *
from pyfhirsdc.serializers.inputFile import parse_sheets, read_input_file
from pyfhirsdc.services.generateActivities import generate_activities
from pyfhirsdc.services.generateCodeSystem import generate_custom_code_system
from pyfhirsdc.services.generateLibraries import generate_libraries
from pyfhirsdc.services.generateValueSet import generate_value_sets

from .generatePlanDefinitions import generate_plandefinitions
from .generateProfiles import generate_profiles
from .generateQuestionnaires import generate_questionnaires


def process_input_file(conf):
    # Read the config file
    config_obj = read_config_file(conf)
    if config_obj is None:
        exit()
    else:
        input_file = read_input_file(get_processor_cfg().inputFile)
        if input_file is not None:
            parse_sheets(input_file, get_processor_cfg().excudedWorksheets)        
            input_file.close()
            
            # generate the CodeSystem
            generate_custom_code_system()  
            # generate questionnaire
            generate_questionnaires()
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

            # Bundle https://github.com/jkiddo/ember



