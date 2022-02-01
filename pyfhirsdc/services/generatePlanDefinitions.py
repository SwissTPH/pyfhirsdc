
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg, get_defaut_fhir
from pyfhirsdc.converters.toQuestionnaire import convert_df_to_questionitems
from pyfhirsdc.serializers.json import get_path_or_default, read_resource
from fhir.resources.plandefinition import PlanDefinition
from .processDecisionTables import processDecisionTableSheet
from .processDecisionTables import processDecisionTable

from ..converters.to_CQL import write_library_CQL, write_action_condition, \
    write_libraries, write_plan_definitions, write_plan_definition_index,\
        writeLibraryHeader
import os
import json

def generate_plandefinitions(decisionTable):
    for name, questions in decisionTable.items():
        generate_plandefinition(name ,questions)

# @param config object fromn json
# @param name string
# @param questions DataFrame
def generate_plandefinition( name ,df_actions):
    # try to load the existing questionnaire
    
    filename =  "plandefinition-" + name + ".json"
    # path must end with /
    path = get_path_or_default(get_fhir_cfg().planDefinition.outputPath, "resource/plandefinition/")
    filepath =os.path.join(get_processor_cfg().outputDirectory , path , filename)
    if not os.path.exists(path):
        os.makedirs(path)
    print('processing plandefinition ', name)
    # read file content if it exists
    pd = init_pd(filepath)
    skipcols=get_processor_cfg().skipcols
    skiprows = get_processor_cfg().skiprows

    if (skipcols == 1):
        df_actions.drop(df_actions.columns[[0]], axis=1, inplace=True)
    elif (skipcols > 1 ):
        df_actions.drop(df_actions.columns[[0,skipcols-1]], axis=1, inplace = True)
    dict_questions = df_actions.to_dict('index')

    ## generate libraries, plandefinitions and libraries
    plandefinitions, libraryCQL, libraries = processDecisionTableSheet(pd,dict_questions,path)
    # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
    #plan_definition = processDecisionTable(plandefinitions, dict_questions)
    
    # write file
    write_plan_definitions(plandefinitions, get_processor_cfg().encoding, path)
    write_plan_definition_index(plandefinitions, path)
    write_libraries(path,libraries,get_processor_cfg().encoding)
    write_library_CQL(path, libraryCQL)
    ##with open(filepath, 'w') as json_file:
    ##    json_file.write(plan_definition.json( indent=4))



def init_pd(filepath):
    pd_json = read_resource(filepath, "PlanDefinition")
    default =get_defaut_fhir('planDefinition')
    if pd_json is not None :
        pd = PlanDefinition.parse_raw( json.dumps(pd_json))  
    elif default is not None:
        # create file from default
        pd = PlanDefinition.parse_raw( json.dumps(default))
    else: pd = PlanDefinition.construct() 

    return pd
    

