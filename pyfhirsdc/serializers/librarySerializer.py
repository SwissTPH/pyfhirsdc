import os
import re
import pandas as pd
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.utils import clean_name, get_codableconcept_code, get_resource_url
from fhir.resources.library import Library
from fhir.resources.attachment import Attachment
from fhir.resources.fhirtypes import Canonical
from fhir.resources.identifier import Identifier
from fhir.resources.parameterdefinition  import ParameterDefinition 
from fhir.resources.identifier import Identifier
from fhir.resources.datarequirement  import DataRequirement, DataRequirementCodeFilter
from .utils import reindent

### Function that creates the constant part of cql files 


def getIdentifierFirstRep(planDef):
    if (not planDef.identifier):
        identifier = Identifier.construct()
        planDef.identifier = [identifier]
    return planDef.identifier[0]  

def generate_plan_defnition_lib(planDefinition, df_actions):
    id = clean_name(planDefinition.id)
    print("Generating library ", planDefinition.name, ".......")
    library = Library(
        id = id,
        identifier = [getIdentifierFirstRep(planDefinition)],
        status = 'active',
        name = planDefinition.name,
        version = " " + get_fhir_cfg().version,
        title = planDefinition.title,
        description = planDefinition.description,
        url = get_resource_url('Library', id),
        content = [Attachment(
            id = "ig-loader-" + id + ".cql"
        )],
        type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'
        ),
        parameter=get_lib_parameters(df_actions),
        dataRequirement= get_lib_data_requirement(df_actions)

    )
    libraryCanonical = Canonical(library.url)
    if not planDefinition.library: 
        planDefinition.library = []    
        planDefinition.library.append(libraryCanonical)

    
    return  library

def get_lib_parameters(df_actions):
    parameters = []
    df = df_actions[df_actions.parentActionId != "{{library}}"]
    for index, row in df.iterrows():
        parameters.append(ParameterDefinition(
            use = 'out',
            name = row['id'],
            type = "boolean"
        ))
        if pd.notna(row['description']):
            parameters.append(ParameterDefinition(
                use = 'out',
                name = row['description'],
                type = "boolean"
            ))
        #TODO add observation, condition and Zscore function parsing here     
    if len(parameters)>0:
        return parameters
    
def get_lib_data_requirement(df_actions):
    data_requirements = []
    Patient = True
    Encounter = True
    df = df_actions[df_actions.parentActionId != "{{library}}"]
    for index, row in df.iterrows():
        if Patient and check_expression_keyword(row, "Patient"):
            Patient = False
            data_requirements.append(
                DataRequirement(
                    type = "Patient",
                    profile = [ Canonical("http://hl7.org/fhir/StructureDefinition/Patient") ]
                )
            )
        if Encounter and check_expression_keyword(row, "Encounter"):
            Encounter = False
            data_requirements.amend(
                DataRequirement(
                    type = "Encounter",
                    profile = [ Canonical("http://hl7.org/fhir/StructureDefinition/Encounter") ]
                )
            )
        # baseEMCare
        codes = get_patient_observation_codes(row)
        for code in codes:
            data_requirements.amend(
                DataRequirement(
                    type = "Observation",
                    profile = [ Canonical("http://hl7.org/fhir/StructureDefinition/Observation") ],
                    mustSupport = [ "code", "encounter.reference", "encounter", "value", "status" ],
                    codeFilter = DataRequirementCodeFilter(
                    path = "code",
                    code = code
                    )
                )
            )
        #TODO add condition and Zscore function parsing here     
    if len(data_requirements)>0:
        return data_requirements

def get_patient_observation_codes(row):
    list_list = []
    codes = []
    for exp in ROW_EXPRESSIONS:
        if pd.notna(row[exp['name']]):
            matches = re.findall("PatientHas\w*Observation\w*\(P<list>[\[\{]([^\]\})]+)[\]\})]",row[exp['name']] )
            for match in matches:
                list_list.append( match.groupdict()['list'])
    for code_list in list_list:
        code_list = code_list.split(',')
        for code in code_list:
            if code not in codes:
                codes.append(code)
    return codes
    
ROW_EXPRESSIONS = [
    
    {'name':'startExpressions', 'prefix':'start::', 'kind':'start'},
    {'name':'stopExpressions', 'prefix':'stop::', 'kind':'stop'},
    {'name':'applicabilityExpressions', 'prefix':'', 'kind':'applicability'}
]

def check_expression_keyword(row, keword):
    for exp in ROW_EXPRESSIONS:
        if pd.notna(row[exp['name']]) and keword in row[exp['name']]:
            return True
    
def writeLibraryHeader(planDefinition):
    return """
library {1}
using FHIR version {0}
include FHIRHelpers version '{0}'
//i nclude {2}Base called Base
//i nclude {2}Concepts called Cx
//i nclude {2}DataElements called Dx
context Patient

""".format(get_fhir_cfg().version, planDefinition.id, get_processor_cfg().scope)

  
def write_library_CQL(output_path, lib, cql):
    if cql is not None and len(cql)>0:
        output_file_path = os.path.join(output_path, lib.name + ".cql")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        for entry in cql:    
            output.write(cql[entry])
            
## function definition from 
# https://hapifhir.io/hapi-fhir//apidocs/hapi-fhir-structures-r4/src-html/org/hl7/fhir/r4/model/PlanDefinition.html#line.4284
## missing in the python library
def write_cql_pd(planDefinition):
    # write 3 cql : start, end, applicability
    cql = {}
    cql['header'] = writeLibraryHeader(planDefinition,)
    i = 0
    list_actions = planDefinition.action
    if list_actions:
        for action in list_actions:
            if (action and action.condition):       
                action_cql = write_action_condition(action)
                if action_cql is not None:
                    cql[i] = action_cql
                    i = i+1
    return cql                
    
def write_action_condition(action):
    cql = ""
    if action.description is not None:
        for condition in action.condition:
            ## Output false, manual process to convert the pseudo-code to CQL
            cql += "/*\n \"{0}\":\n ".format(condition.expression.description if condition.expression.description is not None else action.description)+"\n */\n "+\
                "define \"{0}\":\n ".format(condition.expression.expression)+ \
                    "  false" + "\n\n "
    return cql    

def write_cql_df(plandefinition, df_actions):
    cql = {}
    cql['header'] = writeLibraryHeader(plandefinition)
    i = 0
    if len(df_actions)>0:
        for index, row in df_actions.iterrows():
            # applicability -> "id" : cql
            # start -> "start::id" : cql
            # end -> "end::id" : cql
            if pd.notna(row['stopExpressions']):
                cql[i] = write_cql_action(row['id'], row['description'], 'stop::', row['stopExpressions'])
                i += 1
            if pd.notna(row['startExpressions']):
                cql[i] = write_cql_action(row['id'], row['description'], 'start::', row['startExpressions'])
                i += 1
            if pd.notna(row['applicabilityExpressions']):
                cql[i] = write_cql_action(row['id'], row['description'], '', row['applicabilityExpressions'])
                i += 1
                # add the wrapper name -> id
                cql[i] = write_cql_action(row['description'], '', '','"'+row['id']+'"')
                i += 1
    return cql

def write_cql_action(id, name, prefix, expression):
    return  """
/* {1}{0} : {2}*/
define "{1}{0}":
{3}
""".format(id, prefix, name,reindent(expression,4))

