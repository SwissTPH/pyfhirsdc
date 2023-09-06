

import json
import logging
import os

from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.meta import Meta
from fhir.resources.R4B.plandefinition import PlanDefinition

from pyfhirsdc.config import (get_defaut_fhir, get_dict_df, get_fhir_cfg,
                              get_processor_cfg)
from pyfhirsdc.converters.libraryConverter import generate_attached_library
from pyfhirsdc.converters.planDefinitionConverter import process_decisiontable
from pyfhirsdc.converters.utils import adv_clean_name, clean_name, get_resource_url
from pyfhirsdc.serializers.planDefinitionIndexSerializer import \
    write_plan_definition_index
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")

def generate_plandefinitions():
    decisionTable = get_dict_df()['decisions_tables']
    root_output_path = get_processor_cfg().outputPath
    plandefinitions = {}

    for name, questions in decisionTable.items():
        plandefinitions[name] = generate_plandefinition(name ,questions)
        
    if not os.path.exists(root_output_path):
        os.makedirs(root_output_path)
    write_plan_definition_index(plandefinitions, root_output_path)
    

# @param config object fromn json
# @param name string
# @param questions DataFrame
def generate_plandefinition( name,df_actions):
    # try to load the existing questionnaire
        # path must end with /
    filepath = get_resource_path("PlanDefinition", get_processor_cfg().scope.lower())
    df_actions=df_actions.dropna(axis=0, subset=['id'])
    logger.info('processing plandefinition {0}'.format(name))
    # read file content if it exists
    pd_df = init_pd(filepath)
    skipcols=get_processor_cfg().skipcols
    skiprows = get_processor_cfg().skiprows

    if (skipcols == 1):
        df_actions.drop(df_actions.columns[[0]], axis=1, inplace=True)
    elif (skipcols > 1 ):
        df_actions.drop(df_actions.columns[[0,skipcols-1]], axis=1, inplace = True)
    
    dict_actions = df_actions.to_dict('index')

    ## generate libraries, plandefinitions and libraries
    planDefinitionId = clean_name(name)
    pd_df.title = planDefinitionId
    identifier = Identifier.construct()
    identifier.use = "official"
    identifier.value = planDefinitionId
    pd_df.identifier=[identifier]
    pd_df.id= planDefinitionId

    pd_df.name = planDefinitionId
    pd_df.url = get_resource_url("PlanDefinition", planDefinitionId)
    planDefinition = process_decisiontable(pd_df, df_actions)
     
    if planDefinition is not None:
        library = generate_attached_library(planDefinition,df_actions)
        # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
        #plan_definition = process_decisiontable(plandefinitions, dict_actions)
        # write file
        write_resource(filepath, planDefinition, get_processor_cfg().encoding)

    return planDefinition



def init_pd(filepath):
    pd_json = None #read_resource(filepath, "PlanDefinition") FIXME lib extenstion keep adding itself
    default =get_defaut_fhir('PlanDefinition')
    if pd_json is not None :
        pd = PlanDefinition.parse_raw( json.dumps(pd_json))  
    elif default is not None:
        # create file from default
        pd = PlanDefinition.parse_raw( json.dumps(default))
    else: pd = PlanDefinition.construct() 

    pd.version = get_fhir_cfg().lib_version
    return pd
    

