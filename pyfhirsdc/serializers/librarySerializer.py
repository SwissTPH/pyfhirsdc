import os
import re
import pandas as pd
from pyfhirsdc.config import get_defaut_path, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import add_library_extentions
from pyfhirsdc.converters.mappingConverter import inject_config
from pyfhirsdc.converters.utils import clean_group_name, clean_name, get_codableconcept_code, get_resource_url
from fhir.resources.library import Library
from fhir.resources.attachment import Attachment
from fhir.resources.fhirtypes import Canonical
from fhir.resources.identifier import Identifier
from fhir.resources.parameterdefinition  import ParameterDefinition 
from fhir.resources.identifier import Identifier
from fhir.resources.datarequirement  import DataRequirement, DataRequirementCodeFilter
from .utils import reindent, write_resource

### Function that creates the constant part of cql files 


def getIdentifierFirstRep(planDef):
    if (not planDef.identifier):
        identifier = Identifier.construct()
        planDef.identifier = [identifier]
    return planDef.identifier[0]  

def generate_plan_defnition_lib(resource, df_actions, type = 'pd'):
    id = clean_name(resource.id)
    print("Generating library ", resource.name, ".......")
    library = Library(
        id = id,
        identifier = [],
        status = 'active',
        name = resource.name,
        version = " " + get_fhir_cfg().version,
        title = resource.title,
        description = resource.description,
        url = get_resource_url('Library', id),
        content = [Attachment(
            id = "ig-loader-" + id + ".cql"
        )],
        type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'
        ),
        parameter=get_lib_parameters(df_actions, type),
        dataRequirement= get_lib_data_requirement(df_actions, type)

    )
    cql=write_cql_df(resource, df_actions, type)
    if len(cql)>1:
        output_lib_path = os.path.join(
                get_processor_cfg().outputPath,
                get_fhir_cfg().Library.outputPath
            )
        output_lib_file = os.path.join(
                output_lib_path,
                "library-"+ resource.id +  "." + get_processor_cfg().encoding
            )
        write_resource(output_lib_file, library, get_processor_cfg().encoding)
        cql_path = get_defaut_path('CQL', 'cql')
        write_library_CQL(cql_path, library, cql)
        libraryCanonical = Canonical(library.url)
        if hasattr(resource, 'library') and resource.library is None: 
            resource.library = []    
            resource.library.append(libraryCanonical)
        else:
            resource = add_library_extentions(resource, library.id)

        return  library

def get_lib_parameters_list(df_in, type = "pd"):
    parameters = []
    df = filter_df(df_in,type)

    for index, row in df.iterrows():
        name = row['id'] if 'id' in row else index
        if name is not None and pd.notna(name):
            desc = row['description'].replace(u'\xa0', u' ').replace('  ',' ') if 'description' in row and pd.notna(row['description']) else None
            parameters.append({'name': name, 'type':'boolean'})
            if row['description'] is not None:
                parameters.append({'name':desc, 'type':'boolean'})
    #TODO add observation, condition and Zscore function parsing here   maybe using {{paramter}}  

    return parameters
        
        
def get_lib_parameters(df_in, type = "pd"):
    parameters = []
    parameters_in = get_lib_parameters_list(df_in,type)
    for param in  parameters_in:
        parameters.append(ParameterDefinition(
            use = 'out',
            name = param["name"] ,
            type = param["type"]
        ))

    if len(parameters)>0:
        return parameters
    
def filter_df(df_in,type):    
    if type == "pd":
        df = df_in[df_in.parentId != "{{library}}"]
    elif type == "q":
        df = df_in[df_in.initialExpression.notna() ]
    return df
        
        
def get_lib_data_requirement(df_in, type = 'pd'):
    data_requirements = []
    Patient = True
    Encounter = True
    df = filter_df(df_in,type)
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
            data_requirements.append(
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
    for name, exp in ROW_EXPRESSIONS.items():
        if name in row and pd.notna(row[name]):
            matches = re.findall("Has\w*Obs\w*\(P<list>[\[\{]([^\]\})]+)[\]\})]",row[name] )
            for match in matches:
                list_list.append( match.groupdict()['list'])
    for code_list in list_list:
        code_list = code_list.split(',')
        for code in code_list:
            if code not in codes:
                codes.append(code)
    return codes
    
ROW_EXPRESSIONS = {
    
    'startExpressions': {'col':'startExpressions', 'prefix':'start::', 'kind':'start'},
    'stopExpressions':{'col':'stopExpressions', 'prefix':'stop::', 'kind':'stop'},
    'applicabilityExpressions':{'col':'applicabilityExpressions', 'prefix':'', 'kind':'applicability'},
    'initialExpression':{'col':'initialExpression', 'prefix':'', 'kind':''},
    'id':{'col':'description', 'prefix':'', 'kind':''}
    
}


    

def check_expression_keyword(row, keword):
    for name, exp in ROW_EXPRESSIONS.items():
        if name in row and pd.notna(row[name]) and keword in row[name]:
            return True
    
    
# libs [{name,version,alias}]
# parameters [{name,type}]
def writeLibraryHeader(resource, libs = [], parameters = []):
    return """library {1}
using FHIR version '{0}'
include FHIRHelpers version '4.0.1' called FHIRHelpers 
{3}
{4}
context Patient

""".format(
    get_fhir_cfg().version, 
    clean_group_name(resource.id), 
    get_processor_cfg().scope,
    get_include_lib(libs),
    '')#get_include_parameters(parameters))


# libs is a list {name='', version='', alias = ''}
def get_include_lib(libs):
    ret = ''
    for lib in libs:
        if 'name' in lib and lib['name'] is not None and len(lib['name'])>0:
            ret+="include {}".format(lib['name'])
            if 'version' in lib and lib['version'] is not None and len(lib['version'])>0:
               ret+=" version '{}'".format(lib['version'])
            if 'alias' in lib and lib['alias'] is not None and len(lib['alias'])>0:
               ret+=" called {}".format(lib['alias'])   
            ret+="\n"
    return ret

def get_include_parameters(parameters):
    ret = ''
    for param in parameters:
        ret += "parameter '{}' : {}\n".format(param['name'], param['type'])

    return ret    

def write_library_CQL(output_path, lib, cql):
    if cql is not None and len(cql)>1:
        output_file_path = os.path.join(output_path,  lib.name + ".cql")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        output = open(output_file_path, 'w', encoding='utf-8')
        output.write(cql['header'])
        for entry in cql:
            if entry != 'header':   
                output.write(cql[entry])
            
## function definition from 
# https://hapifhir.io/hapi-fhir//apidocs/hapi-fhir-structures-r4/src-html/org/hl7/fhir/r4/model/PlanDefinition.html#line.4284
## missing in the python library
def write_cql_pd(planDefinition):
    # write 3 cql : start, end, applicability
    cql = {}
    cql['header'] = writeLibraryHeader(planDefinition)
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



def write_cql_df(resource, df_actions,  type):
    cql = {}
    libs = []
    i = 0
    oi = i
    df_main = df_actions.dropna(axis=0, subset='id')
    if len(df_actions)>0:
        for index, row in df_main.iterrows():
            ref = row['id'] if 'id' in row else index 
            if index == "{{library}}" or "id" in row and pd.notna(row['id']) and row['id'] == "{{library}}":
                details =  row['description'].split("::")
                name = details[0]
                version = details[2] if len(details)>2 else None
                alias = details[1] if len(details)>1 else None
                libs.append({
                    'name':name,
                    'version':version,
                    'alias':alias
                })
            # PlanDefinition CQL
            # applicability -> "id" : cql
            # start -> "start::id" : cql
            # end -> "end::id" : cql
            if 'stopExpressions' in row and pd.notna(row['stopExpressions']):
                cql[i] = write_cql_action(ref, row,'stopExpressions', df_actions)
                
                i += 1
            if 'startExpressions' in row and pd.notna(row['startExpressions']):
                cql[i] = write_cql_action(ref, row,'startExpressions', df_actions)
                i += 1
            if 'applicabilityExpressions' in row and pd.notna(row['applicabilityExpressions']):
                cql[i] = write_cql_action(ref, row,'applicabilityExpressions', df_actions)
                i += 1
                # add the wrapper name -> id
                cql[i] = write_cql_action(row['description'], row, 'id', df_actions)
                i += 1
            ## questionnaire initial expression in CQL, FIXMDe
            if 'initialExpression' in row and pd.notna(row['initialExpression']) and not re.match("^(uuid)\(\)$",row['initialExpression'].strip()):
                cql[i] = write_cql_action(ref, row,'initialExpression',df_actions)
                i += 1
            if i > oi :
                # FIXME, need better way to detect Base
                cql[i-1] = inject_config(cql[i-1].replace("PatientHas", "Base.PatientHas"))
            oi = i
    cql['header'] = writeLibraryHeader(resource, libs, get_lib_parameters_list(df_actions, type ))
    return cql

def write_cql_action(id, row, expression_column, df):
    
    cql_exp = row[expression_column] if row[expression_column].strip() != '{{cql}}' else ''
    prefix = ROW_EXPRESSIONS[expression_column]['prefix']
    # to create the reverse rule
    name = row['description'] if  row['description']!= id  else row['id']
    ret =   """
/* {1}{0} : {2}*/
define "{1}{0}":

""".format(id, prefix, name,reindent(cql_exp,4))
    sub =  get_additionnal_cql(id,df,expression_column)
    if len(sub)>0 and cql_exp != '':
        ret +=reindent("({})\n AND\n ({})\n".format(cql_exp,sub),4)
    elif len(sub)>0:
        ret +=reindent("{}\n".format(sub),4)
    elif cql_exp != '':    
        ret +=reindent("{}\n".format(cql_exp),4)
    return ret
    

def get_additionnal_cql(id,df,expression_column ):
    ret = ''
    
    if 'parentId' in df and 'type' in df:
        df_details = df[(df['type'] == '{{cql}}') & (df['parentId'] == id)]
        len_df =  len(df_details)
        count_i = 0
        if len_df>0:
            for index, row in df_details.iterrows():
                if expression_column in row and pd.notna(row[expression_column]):
                    cql_exp = row[expression_column] if row[expression_column].strip() != '{{cql}}' else ''
                    if count_i>0:
                        ret += " OR \n" 
                    sub =  get_additionnal_cql(row['id'],df,expression_column)
                    if len(sub)>0:
                        ret +=reindent("({})\n AND\n ({})\n".format(cql_exp,sub),4)
                    else:
                        ret +=reindent("{}\n".format(cql_exp),4)
                    count_i += 1

    


    return ret



