import os
import re
from xmlrpc.client import boolean

import pandas as pd
from fhir.resources.attachment import Attachment
from fhir.resources.datarequirement import (DataRequirement,
                                            DataRequirementCodeFilter)
from fhir.resources.fhirtypes import Canonical
from fhir.resources.identifier import Identifier
from fhir.resources.library import Library
from fhir.resources.parameterdefinition import ParameterDefinition

from pyfhirsdc.config import (append_used_obs, append_used_valueset,
                              get_defaut_path, get_fhir_cfg, get_processor_cfg,
                              get_used_obs, get_used_valueset)
from pyfhirsdc.converters.extensionsConverter import add_library_extentions
from pyfhirsdc.converters.questionnaireItemConverter import \
    get_question_fhir_data_type
from pyfhirsdc.converters.utils import (clean_group_name, clean_name,
                                        get_codableconcept_code,
                                        get_custom_codesystem_url,
                                        get_resource_url, inject_config)

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
    lib_id =clean_group_name(id)
    library = Library(
        id = lib_id,
        status = 'active',
        name = lib_id,
        version = get_fhir_cfg().lib_version,
        title = resource.title,
        description = resource.description,
        url = get_resource_url('Library', lib_id),
        content = [Attachment(
            id = "ig-loader-" + lib_id + ".cql"
        )],
        type = get_codableconcept_code( 
            "http://hl7.org/fhir/ValueSet/library-type", 
            'logic-library'
        ),
        parameter=get_lib_parameters(df_actions, type),
        dataRequirement= get_lib_data_requirement(df_actions, type),
        identifier=[Identifier(
            use = 'official',
            value = id
        )]

    )
    cql=write_cql_df(library, df_actions, type)
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
        if type == "q":
            q_type = get_question_fhir_data_type(row['type'])
        else:
            q_type = 'boolean'
        name = row['id'] if 'id' in row else index
        if name is not None and pd.notna(name):
            desc = row['label'].replace(u'\xa0', u' ').replace('  ',' ') if 'label' in row and pd.notna(row['label']) else\
                row['description'].replace(u'\xa0', u' ').replace('  ',' ') if 'description' in row and pd.notna(row['description']) else None
            parameters.append({'name': name, 'type':q_type})
            if row['description'] is not None:
                parameters.append({'name':desc, 'type':q_type})
    #TODO add observation, condition and Zscore function parsing here   maybe using {{paramter}}  

    return parameters

MAPPING_TYPE_LIB ={
    "choice":"code",
    "mapping":"boolean",
    "quantity":"Quantity"
}

def get_lib_type(type):
    if type in MAPPING_TYPE_LIB:
        return MAPPING_TYPE_LIB[type]
    elif type ==None:
        return 'boolean'
    else:
        return type
        
def get_lib_parameters(df_in, type = "pd"):
    parameters = []
    parameters_in = get_lib_parameters_list(df_in,type)
    for param in  parameters_in:
        parameters.append(ParameterDefinition(
            use = 'out',
            name = param["name"] ,
            type = get_lib_type(param["type"])
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
            matches = re.findall("Has\w*Obs\w*\(?P<list>[\[\{]([^\]\})]+)[\]\})]",row[name] )
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
def writeLibraryHeader(library, libs = [],  parameters = []):
    return """/*
@author: Patrick Delcroix
@description: This library is part of the project {3}
*/
library {1} version '{2}'
using FHIR version '{0}'
include FHIRHelpers version '{0}' called FHIRHelpers 
{4}
{5}
context Patient
      
""".format(
    get_fhir_cfg().version, 
    library.name, 
    get_fhir_cfg().lib_version, 
    get_processor_cfg().scope,
    get_include_lib(libs, library),
    '')#get_include_parameters(parameters))


# libs is a list {name='', version='', alias = ''}
def get_include_lib(libs, library = None):
    ret = ''
    for lib in libs:
        if 'name' in lib and lib['name'] is not None and len(lib['name'])>0:
            ret+="include {}".format(lib['name'])
            if 'version' in lib and lib['version'] is not None and len(lib['version'])>0:
               ret+=" version '{}'".format(lib['version'].replace("{{LIB_VERSION}}",get_fhir_cfg().lib_version).replace("{{FHIR_VERSION}}",get_fhir_cfg().version))
            else:
                print("error version missing for {} but mandatory as dependency for library {}".format(lib['name'], library.name))
                exit()
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
def write_cql_pd(library, planDefinition):
    # write 3 cql : start, end, applicability
    cql = {}
    cql['header'] = writeLibraryHeader(library)
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


def get_observation_cql_from_concepts(concepts, lib):
    # write 3 cql : start, end, applicability
    list_of_display = []
    cql = {}
    libs = [{'name':'EmCareBase','alias':'B','version':get_fhir_cfg().lib_version}]
    cql['header'] = writeLibraryHeader(lib, libs)
    i = 0
    if concepts is not None:
        for concept in concepts:
            concept.display=str(concept.display).lower()
            if concept.display not in list_of_display:
                list_of_display.append(concept.display)
                if (concept is not None and concept.code is not None):       
                    concept_cql = write_obsevation(concept)
                    if concept_cql is not None:
                        append_used_obs(concept.code)
                        append_used_obs(concept.display)
                        cql[i] = concept_cql
                        i = i+1
            else:
                print("Warning: {} is defined multiple times".format(concept.display))
    return cql    

def get_valueset_cql_from_concepts(concepts, lib):
    # write 3 cql : start, end, applicability
    cql = {}
    list_of_display = []
    libs = [{'name':'EmCareBase','alias':'B','version':get_fhir_cfg().lib_version}]
    cql['header'] = writeLibraryHeader(lib, libs)
    i = 0
    if concepts:
        for concept in concepts:
            concept.display=str(concept.display).lower()
            if concept.display not in list_of_display:
                list_of_display.append(concept.display)
                if (concept and concept.code):    
                    concept_cql = write_valueset(concept)
                    if concept_cql is not None:
                        append_used_valueset(concept.code)
                        append_used_valueset(concept.display)
                        cql[i] = concept_cql
                        i = i+1
            else:
                print("Warning: {} is defined multiple times".format(concept.display))
    return cql    

def write_valueset(concept):
    cql = ""
    if concept.display is not None:
        ## Output false, manual process to convert the pseudo-code to CQL
        cql += "define \"{0}\":\n".format(concept.display)+ \
                "  B.c('{}')".format(concept.code) + "\n\n "
    return cql
  
def write_obsevation(concept):
    cql = ""

    if concept.display is not None and pd.notna(concept.display):
        ## Output false, manual process to convert the pseudo-code to CQL
        cql += "/*\"{0}\"*/\n".format(concept.display)+\
            "define \"{0}\":\n".format(str(concept.display).lower())+ \
                "  B.HasObs(B.c('{}'), '{}')".format(concept.code,get_custom_codesystem_url()) + "\n"
    if concept.code is not None and concept.code:
        ## Output false, manual process to convert the pseudo-code to CQL    
        cql += "define \"{0}\":\n".format(str(concept.code).lower())+ \
                "  B.HasObs(B.c('{}'), '{}')".format(concept.code, get_custom_codesystem_url()) + "\n\n"
    return cql    



def write_action_condition(action):
    cql = ""
    if action.description is not None:
        for condition in action.condition:
            
            ## Output false, manual process to convert the pseudo-code to CQL
            cql += "/*\n \"{0}\":\n ".format(condition.expression.description if condition.expression.description is not None else action.description)+"\n */\n "+\
                "define \"{0}\":\n ".format(str(condition.expression.expression).lower())+ \
                    "  false" + "\n\n "
    return cql    



def write_cql_df(library, df_actions,  type):
    cql = {}
    libs = [            {
                'name':get_processor_cfg().scope+"Base",
                'version':get_fhir_cfg().lib_version,
                'alias':"Base"
            },{
                'name':get_processor_cfg().scope+"Observation",
                'version':get_fhir_cfg().lib_version,
                'alias':"obs"
            },{
                'name':get_processor_cfg().scope+"ValueSet",
                'version':get_fhir_cfg().lib_version,
                'alias':"val"
            }]
        
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
                cql[i] = write_cql_action(ref, row, 'applicabilityExpressions', df_actions,row['description'])
                i += 1
            ## questionnaire initial expression in CQL, FIXMDe
            if 'initialExpression' in row and pd.notna(row['initialExpression']) and not re.match("^(uuid)\(\)$",row['initialExpression'].strip()) and row['type'] != '{{cql}}' :
                cql[i] = write_cql_action(ref, row,'initialExpression',df_actions)
                i += 1
                if pd.notna(row['label']):
                    cql[i] = write_cql_action(ref, row, 'initialExpression', df_actions,row['label'])
                    i += 1
            while  i > oi :
                cql[oi] = inject_config(cql[oi])
                oi+=1

    
    cql['header'] = writeLibraryHeader(library, libs, get_lib_parameters_list(df_actions, type ))
    return cql

def write_cql_action(id, row, expression_column, df, display = None):
    if display is None:
        display = id   
    cql_exp = row[expression_column] if row[expression_column].strip() != '{{cql}}' else ''
    if cql_exp != '':
        cql_exp = map_to_obs_valueset(cql_exp)
    prefix = ROW_EXPRESSIONS[expression_column]['prefix']
    # to create the reverse rule
    name = row['label'] if "label" in row else row['description'] if row['description']!= id  else row['id']
    ret =   """
/* {1}{0} : {2}*/
define "{1}{0}":
""".format(str(display).lower(), str(prefix).lower(), name)
    sub =  get_additionnal_cql(id,df,expression_column)
    sub = map_to_obs_valueset(sub)
    if len(sub)>0 and cql_exp != '':
        ret +=reindent("({})\n and ({})\n".format(cql_exp,sub),4)
    elif len(sub)>0:
        ret +=reindent("{}\n".format(sub),4)
    elif cql_exp != '':    
        ret +=reindent("{}\n".format(cql_exp),4)
    return ret + "\n"

def map_to_obs_valueset(cql_exp):
    # find "([^"]+)" *= *"([^"]+)" 
    valueset_list = [x.lower() for x in  get_used_valueset()]
    obs_list = [x.lower() for x in get_used_obs()]
    changed = []
    matches = re.findall(r'(?<!\.)"([^"\.]+)"',cql_exp)
    out = cql_exp
    out = out.replace('HasCond', 'Base.HasCond')
    out = out.replace('HasObs', 'Base.HasObs')
    for match in matches:
        if match not in changed:
            if match  in ("Yes", "No"):
                out = out.replace('"{}"'.format(match), 'Base."{}"'.format(match) )
                changed.append(match)
            elif match.lower() in valueset_list:
                changed.append(match)
                out = out.replace('"{0}"'.format(match), 'val."{1}"'.format(match,match.lower()) )
            elif match.lower() in obs_list:
                changed.append(match)
                out = out.replace('"{0}"'.format(match), 'obs."{1}"'.format(match,match.lower()) )
            else:
                out = out.replace('"{0}"'.format(match), '"{1}"'.format(match,match.lower()) )
            
    
    return out
    

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
                        ret += "\n or " 
                    sub =  get_additionnal_cql(row['id'],df,expression_column)
                    if len(sub)>0:
                        ret +=reindent("({})\n and ({})\n".format(cql_exp,sub),4)
                    else:
                        ret +=reindent("{}\n".format(cql_exp),4)
                    count_i += 1
            return ret
    return ''



