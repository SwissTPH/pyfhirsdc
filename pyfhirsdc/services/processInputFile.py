from pyfhirsdc.serializers.configFile import read_config_file
from pyfhirsdc.serializers.inputFile import read_input_file, parse_sheets

from .generateExtensions import generate_extensions

import os
import pandas as pd
import re

def process_input_file(conf):
    # Read the config file
    config = read_config_file(conf)
    if config is None:
        exit()
    else:
        inputFile = read_input_file(config.processor.InputFile)
        if inputFile is not None:
            questionnaires, decision_tables,\
                value_set, care_plan, settings,\
                choice_column, cql = parse_sheets(inputFile, config.processor.excudedWorksheets)        
            # generate extension
            extensions = generate_extensions(questionnaires)

            # generate profiles

            # generate the CodeSystem

            # generate the valueSet

            # generate conceptMap

            # generate the questionnaire

            # generate the DE CQL 

            # generate the Concept CQL 

            # generate planDefinition

            # generate carePlane

