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
                              get_used_obs, get_used_obs_valueset, get_used_valueset)
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

def generate_attached_library(resource, df_actions, type = 'pd'):
    library = generate_library(resource.name, df_actions, type)
    if library is not None:
        libraryCanonical = Canonical(library.url)
        if hasattr(resource, 'library') and resource.library is None: 
            resource.library = []    
            resource.library.append(libraryCanonical)
        else:
            resource = add_library_extentions(resource, library.id)
        
def generate_library(name, df_actions, type = 'pd', description = None):

    id = clean_name(name)
    print("Generating library ", name, ".......")
    lib_id =clean_group_name(id)
    library = Library(
        id = lib_id,
        status = 'active',
        name = lib_id,
        version = get_fhir_cfg().lib_version,
        title = name,
        description = description, # FIXME add sope library
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
                "library-"+ id +  "." + get_processor_cfg().encoding
            )
        write_resource(output_lib_file, library, get_processor_cfg().encoding)
        cql_path = get_defaut_path('CQL', 'cql')
        write_library_CQL(cql_path, library, cql)


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
        if name is not None and pd.notna(name) and '{{' not in name :
            desc = row['label'].replace(u'\xa0', u' ').replace('  ',' ') if 'label' in row and pd.notna(row['label']) else\
                row['description'].replace(u'\xa0', u' ').replace('  ',' ') if 'description' in row and pd.notna(row['description']) else None
            parameters.append({'name': name, 'type':q_type, 'use': 'out'})
            if row['description'] is not None and pd.notna(row['description']):
                parameters.append({'name':desc, 'type':q_type, 'use': 'out'})
    #TODO add observation, condition and Zscore function parsing here   maybe using {{paramter}}  

    return parameters

MAPPING_TYPE_LIB ={
    "choice":"code",
    "mapping":"boolean",
    "quantity":"Quantity",
    'String':'string'
}

def get_lib_type(type):
    if type in MAPPING_TYPE_LIB:
        return MAPPING_TYPE_LIB[type]
    elif type ==None:
        return 'boolean'
    else:
        return type
        
def get_lib_parameters(df_in, type = "pd"):
    parameters = []#ParameterDefinition(
    #        use = 'in',
    #        name = 'encounterid' ,
    #        type = 'string'
    #   )]
    parameters_in = get_lib_parameters_list(df_in,type)
    for param in  parameters_in:
        parameters.append(ParameterDefinition(
            use = 'out',
            name = param["name"].lower() ,
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
def writeLibraryHeader(library, libs = [], other_header='context Patient'):
    return """/*
@author: Patrick Delcroix
@description: This library is part of the project {3}
*/
library {1} version '{2}'
using FHIR version '{0}'
include FHIRHelpers version '{0}' called FHIRHelpers 
{4}

{5}

{6}

""".format(
    get_fhir_cfg().version, 
    library.name, 
    get_fhir_cfg().lib_version, 
    get_processor_cfg().scope,
    get_include_lib(libs, library),
    get_include_parameters(library.parameter),
    other_header)


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
    if parameters is not None:
        for param in parameters:
            if param.use == 'in':
                ret += 'parameter "{}"  {}\n'.format(param.name , param.type)

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


def get_code_cql_from_concepts(concepts, lib):
    # write 3 cql : start, end, applicability
    list_of_display = []
    cql = {}
    libs = []
    cql['header'] = writeLibraryHeader(lib, libs, 
        'codesystem "{}" : \'{}\'\n'.format(get_processor_cfg().scope, get_custom_codesystem_url()) )
    i = 0
    if concepts is not None:
        for concept in concepts:
            concept.display=str(concept.display).lower()
            if concept.display not in list_of_display:
                list_of_display.append(concept.display)
                if (concept is not None and concept.code is not None):       
                    concept_cql = write_code(concept)
                    #concept_cql = write_obsevation(concept)
                    if concept_cql is not None:
                        append_used_obs(concept.code, concept.display)
                        cql[i] = concept_cql
                        i = i+1
            else:
                print("Warning: {} :{} is defined multiple times".format(lib.name,concept.display))
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
            "define \"{0}\":\n".format(str(concept.display).lower().replace("\n", ""))+ \
                "  B.HasObs('{}')".format(concept.code,get_custom_codesystem_url()) + "\n\n"
    if concept.code is not None and concept.code:
        ## Output false, manual process to convert the pseudo-code to CQL    
        cql += "define \"{0}\":\n".format(str(concept.code).lower().replace("\n", ""))+ \
                "  B.HasObs('{}')".format(concept.code, get_custom_codesystem_url()) + "\n\n"
    return cql    

def write_code(concept):
    cql = ""
    if concept.display is not None and pd.notna(concept.display):
        ## Output false, manual process to convert the pseudo-code to CQL
        cql += "code \"{0}\": '{1}' from \"{2}\" display '{3}'\n".format(concept.display.replace('"', '\\"'),concept.code, get_processor_cfg().scope  ,concept.display.replace("'", "\\'"))
        
        return cql


def write_action_condition(action):
    cql = ""
    if action.description is not None:
        for condition in action.condition:
            
            ## Output false, manual process to convert the pseudo-code to CQL
            cql += "/*\n \"{0}\":\n ".format(condition.expression.description if condition.expression.description is not None else action.description)+"\n */\n "+\
                "define \"{0}\":\n ".format(str(condition.expression.expression).lower().replace("\n", ""))+ \
                    "  false" + "\n\n "
    return cql    



def write_cql_df(library, df_actions,  type):
    cql = {}
    libs = [            {
                'name':get_processor_cfg().scope.lower()+"base",
                'version':get_fhir_cfg().lib_version,
                'alias':"Base"
            },{
                'name':get_processor_cfg().scope.lower()+"observation",
                'version':get_fhir_cfg().lib_version,
                'alias':"obs"
            },{
                'name':get_processor_cfg().scope.lower()+"valueset",
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
                if pd.notna(row['description']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['applicabilityExpressions']['prefix'], row['description'].lower(),ref.lower())
                    i += 1
            ## questionnaire initial expression in CQL, FIXMDe
            if 'initialExpression' in row and pd.notna(row['initialExpression']) and not re.match("^(uuid)\(\)$",row['initialExpression'].strip()) and row['type'] != '{{cql}}' :
                cql[i] = write_cql_action(ref, row,'initialExpression',df_actions)
                i += 1
                if pd.notna(row['label']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['initialExpression']['prefix'], row['label'].lower(),ref.lower())
                    i += 1
            while  i > oi :
                cql[oi] = inject_config(cql[oi])
                oi+=1

    
    cql['header'] = writeLibraryHeader(library, libs)
    return cql

def write_cql_action(id, row, expression_column, df, display = None):
    cql_exp = None
    if display is None:
        display = id   
    cql_exp_raw = row[expression_column] if row[expression_column].strip() != '{{cql}}' else ''

        
    
    prefix = ROW_EXPRESSIONS[expression_column]['prefix']
    # to create the reverse rule
    name = row['label'] if "label" in row else row['description'] if row['description']!= id  else row['id']
    sub =  get_additionnal_cql(id,df,expression_column)
    if len(sub)>0 and cql_exp_raw != '':
        cql_exp_raw =reindent("({})\n and ({})\n".format(cql_exp_raw,sub),4)
    elif len(sub)>0:
        cql_exp_raw =reindent("{}\n".format(sub),4)
    elif cql_exp_raw != '':    
        cql_exp_raw =reindent("{}\n".format(cql_exp_raw),4)   
    # translation to CQL function
    if cql_exp_raw != '':
        cql_exp = convert_reference_to_cql(cql_exp_raw,df ) 
    ret =   """
/* 
{1}{0} : {2}
{3}
*/
define "{1}{0}":
{4}
""".format(
    str(display).lower().replace("\n", ""), 
    str(prefix).lower().replace("\n", ""), 
    name,
    cql_exp_raw,
    cql_exp
    )
    return ret


def write_cql_alias(prefix, alias,reference):
    return   """
/* alias {1}{0} : {2}*/
define "{1}{0}":
    "{2}"
""".format(prefix.replace("\n", ""), alias.replace("\n", ""),reference)

def convert_reference_to_cql(cql_exp, df):
    # find "([^"]+)" *= *"([^"]+)" 
    valueset_linkid = [x.lower() for x in  get_used_valueset().keys()]
    valueset_label = [x.lower() for x in  get_used_valueset().values()]
    obs_valueset_linkid = [x.lower() for x in get_used_obs_valueset().keys()]
    obs_valueset_label = [x.lower() for x in get_used_obs_valueset().values()]
    obs_linkid = [x.lower() for x in get_used_obs().keys()]
    obs_label = [x.lower() for x in get_used_obs().values()]
    changed = []
    matches = re.findall(r'([ !=<>voc\.]+)?"([^"\.]+)"',cql_exp)
    out = cql_exp
    out = out.replace('HasCond', 'Base.HasCond')
    out = out.replace('HasObs', 'Base.HasObs')
    out = out.replace('GetObsValue', 'Base.GetObsValue')


    for matching in matches:
        prefix = matching[0][-1] if len(matching[0])>0  else ''
        if prefix != '.':
            operator = bool(re.search('[!=<>]', matching[0]))
            match = matching[1]

            if match not in changed:
                if df is not None and (bool(re.search('[^a-zA-Z]', prefix)) or prefix == '') and  len(df[(df.id == match) | (df.label == match)]):
                    # Localy define variable should NOT be converted but put in lower case
                    out = out.replace('"{}"'.format(match), '"{}"'.format(match.lower()) )
                elif match  in ("Yes"):
                    out = out.replace('"{}"'.format(match), 'true'.format(match) )
                    changed.append(match)
                elif match  in ("No"):
                    out = out.replace('"{}"'.format(match), 'false'.format(match) )
                    changed.append(match)
                # for valueset attached converted in obs
                elif match.lower() in obs_valueset_linkid and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), "Base.GetObsValue('{0}')".format(match) )
                elif match.lower() in obs_valueset_label and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    linkid = list(get_used_obs_valueset().keys())[list(obs_valueset_label).index(match.lower())]
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), "Base.GetObsValue('{0}')".format(linkid) )
                # for valueset
                elif match.lower() in valueset_linkid and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), 'val."{0}"'.format(get_used_valueset()[match].lower()) )
                elif match.lower() in valueset_label and (prefix == 'v'   or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), 'val."{0}"'.format(match.lower()) )
                # for obs
                elif match.lower() in obs_linkid and prefix in ('',' ','o'):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'o' else '',match), "Base.GetObsValue('{0}')".format(match) )
                elif match.lower() in obs_label and prefix in ('',' ','o'):
                    linkid = list(get_used_obs().keys())[list(obs_label).index(match.lower())]
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'o' else '',match), "Base.GetObsValue('{0}')".format(linkid) )
                else:
                     print("Warning: string not translated {} {} ".format(prefix,match))
                    
    # quick fix remove the select multiple
    matches = re.findall(r"(Base\.GetObsValue\('([^']+)'\) *= *Base\.GetObsValue\('([^']+)'\))",out)
    for match in matches:
        replacement = "Base.GetObsValue('{}&{}') = true".format(match[1],match[2])
        print('rework {}-{} is an observation (present) '.format(match[2],get_used_obs()[match[2]] ))
        out = out.replace( match[0], replacement)
    # quick fix remove the select multiple
    matches = re.findall(r"(Base\.GetObsValue\('([^']+)'\) *!= *Base\.GetObsValue\('([^']+)'\))",out)
    for match in matches:
        replacement = "Base.GetObsValue('{}&{}') = false".format(match[1],match[2])
        print('rework {}-{} is an observation (absent)'.format(match[2],get_used_obs()[match[2]] ))
        out = out.replace( match[0], replacement)
    # Base.GetObsValue('EmCare.B15S2.DE09') = val."some mucous membrane pallor"
    matches = re.findall(r"(Base\.GetObsValue\('([^']+)'\) *= *val\.\"([^\"]+)\")",out)
    for match in matches:
        linkid = list(get_used_valueset().keys())[list(valueset_label).index(match[2].lower())]
        replacement = "Base.HasObsValueCode('{}', '{}')".format(match[1],linkid)
        print('rework {0} = val."{1}" to  GetObsValueCode("{0}, "{2}")'.format(match[1],match[2],linkid ))
        out = out.replace( match[0], replacement)
    # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(([a-zA-Z'\(\)_\.]+|\"[^\"]+\") *!= *true)",out)
    for match in matches:
        replacement = "Coalesce({},false)!=true".format(match[1])
        print('rework {0} != true to  Coalesce({0},false)!=true'.format(match[1]))
        out = out.replace( match[0], replacement)
        # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(ToInteger\( *((?:[a-zA-Z'_\.]+(\([^\)]+\))?|\"[^\"]+\")[^\)]*)\))",out)
    for match in matches:
        replacement = "ToInteger(Coalesce({},false))".format(match[1])
        print('rework {0}  to  {1}'.format(match[0],replacement))
        out = out.replace( match[0], replacement)
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
                        ret += ")\n or (" 
                    else:
                        ret += "("
                    sub =  get_additionnal_cql(row['id'],df,expression_column)
                    if len(sub)>0:
                        ret +=reindent("({})\n and ({})\n".format(cql_exp,sub),4)
                    else:
                        ret +=reindent("{}\n".format(cql_exp),4)
                    count_i += 1
            return ret +")"
    return ''



