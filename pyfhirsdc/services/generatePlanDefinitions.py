

from pyfhirsdc.config import get_defaut_path, get_fhir_cfg, get_processor_cfg, get_defaut_fhir
from pyfhirsdc.converters.utils import clean_name, get_resource_url
from pyfhirsdc.serializers.json import  read_resource
from pyfhirsdc.serializers.http import post_cql
from fhir.resources.plandefinition import PlanDefinition
from fhir.resources.library import Library
from fhir.resources.identifier import Identifier
import re
from pyfhirsdc.converters.planDefinitionConverter import   \
      write_plan_definition_index, processDecisionTable
from pyfhirsdc.converters.libraryConverter import  generate_plan_defnition_lib, write_library_CQL
import os
import json

from pyfhirsdc.serializers.utils import  get_resource_path, write_resource, get_cql_files

def generate_plandefinitions(decisionTable):
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
    print('processing plandefinition {0}'.format(name))
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
    planDefinitionId = clean_name(name).lower()
    pd_df.title = planDefinitionId
    identifier = Identifier.construct()
    identifier.use = "official"
    identifier.value = planDefinitionId
    pd_df.identifier=[identifier]
    pd_df.id= planDefinitionId

    pd_df.name = planDefinitionId
    pd_df.url = get_resource_url("PlanDefinition", planDefinitionId)
    planDefinition = processDecisionTable(pd_df, df_actions)
     
    if planDefinition is not None:
        ## Write CQL and library structure 
        cql, library = generate_plan_defnition_lib(planDefinition)
        cql_path = get_defaut_path('CQL', 'cql')
        write_library_CQL(cql_path, library, cql)
        
        ## Get all the cql files from the cql directory
        cql_files = get_cql_files(cql_path)
        ## Build the payload to be sent to the CQL translator. This will send back the library
        ## with the ELM + CQL back
        ## To send multiple different CQL files at once we need to sent is as POST
        ## with a separator and as multipartdata -> here we build it
        multipart_payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW"
        for cql_file in cql_files:
            ## Split string using regex ASSUMPTION: cql files have a line with 
            ## library, one space and the name
            library_name = re.search(r"[\s\S]*(?<=library )([^\s]+)([\s\S]*)",cql_file ).group(1)
            multipart_payload += "\n"+\
                "Content-Disposition: form-data; name={0}".format(library_name)+\
                    "\n"+cql_file
        multipart_payload+="\n"+"------WebKitFormBoundary7MA4YWxkTrZu0gW--"
        libraries = post_cql(multipart_payload, get_fhir_cfg().Library.cql_translator)
        output_lib_path = os.path.join(
                get_processor_cfg().outputPath,
                get_fhir_cfg().Library.outputPath
            )
        output_lib_file = os.path.join(
                output_lib_path,
                "library-"+ name +  "." + get_processor_cfg().encoding
            )
        for library in libraries:
            write_resource(output_lib_file, library, get_processor_cfg().encoding)


        # add the fields based on the ID in linkID in items, overwrite based on the designNote (if contains status::draft)
        #plan_definition = processDecisionTable(plandefinitions, dict_actions)
        # write file
        write_resource(filepath, planDefinition, get_processor_cfg().encoding)
        
        

    return planDefinition



def init_pd(filepath):
    pd_json = read_resource(filepath, "PlanDefinition")
    default =get_defaut_fhir('PlanDefinition')
    if pd_json is not None :
        pd = PlanDefinition.parse_raw( json.dumps(pd_json))  
    elif default is not None:
        # create file from default
        pd = PlanDefinition.parse_raw( json.dumps(default))
    else: pd = PlanDefinition.construct() 

    return pd
    

