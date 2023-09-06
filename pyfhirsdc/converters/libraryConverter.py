### Function that creates the constant part of cql files 
import logging
import os
import re
from xmlrpc.client import boolean
from pyfhirsdc.version import __version__

import pandas as pd
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.datarequirement import (DataRequirement,
                                            DataRequirementCodeFilter)
from fhir.resources.R4B.fhirtypes import Canonical
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.library import Library
from fhir.resources.R4B.parameterdefinition import ParameterDefinition

from pyfhirsdc.config import (get_defaut_path, get_fhir_cfg, get_processor_cfg,
                              get_used_obs, get_used_obs_valueset,
                              get_used_valueset, get_dict_df)
from pyfhirsdc.converters.extensionsConverter import add_library_extensions
from pyfhirsdc.converters.questionnaireItemConverter import \
    get_question_fhir_data_type
from pyfhirsdc.converters.utils import (adv_clean_name, clean_name,get_pyfhirsdc_lib_name,
                                        get_codableconcept_code, get_custom_codesystem_url,
                                        get_resource_url, inject_config,METADATA_CODES)
from pyfhirsdc.serializers.docSerializer import get_doc_table, write_docs
from pyfhirsdc.serializers.librarySerializer import (GETOBS_FORMAT,
                                                     GETOBSCODE_FORMAT,
                                                     GETOBSVALUE_FORMAT,
                                                     VAL_FORMAT,
                                                     write_cql_action,
                                                     write_cql_alias,
                                                     write_library_CQL,
                                                     writeLibraryHeader)
from pyfhirsdc.serializers.utils import reindent, write_resource

logger = logging.getLogger("default")

ROW_EXPRESSIONS = {
    
    'startExpressions': {'col':'startExpressions', 'prefix':'start::', 'kind':'start'},
    'stopExpressions':{'col':'stopExpressions', 'prefix':'stop::', 'kind':'stop'},
    'applicabilityExpressions':{'col':'applicabilityExpressions', 'prefix':'', 'kind':'applicability'},
    'initialExpression':{'col':'initialExpression', 'prefix':'', 'kind':''},
    'id':{'col':'label', 'prefix':'', 'kind':''},
    'enableWhenExpression':{'col':'enableWhenExpression', 'prefix':'', 'kind':'applicability'}
    
}

    

def generate_attached_library(resource, df_actions, type = 'pd'):
    library = generate_library(resource.name, df_actions, type)
    if library is not None:
        if  re.search(get_fhir_cfg().canonicalBase, library.url) and '|' not in library.url :
            libraryCanonical = Canonical(library.url+"|"+get_fhir_cfg().lib_version)
        else:
            libraryCanonical = Canonical(library.url)
        if hasattr(resource, 'library') and resource.library is None: 
            resource.library = []    
            resource.library.append(libraryCanonical)
        else:
            resource = add_library_extensions(resource, libraryCanonical)
        return True
        
def generate_library(name, df_actions, type = 'pd', description = None):

    id = get_pyfhirsdc_lib_name(name)
    logger.info("Generating library " + name + ".......")
    lib_id =adv_clean_name(id)
    library = Library(
        id = lib_id,
        status = 'active',
        name = lib_id,
        version = get_fhir_cfg().lib_version,
        title = name,
        description = description, # FIXME add scope library
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
    
    cql, list_inputs =format_cql_df(library, df_actions, type)
    if type in ('q','c','r'):
        cql['backref'] = write_cql_action(
            'BackReference',
            'back reference to resource', 
            """Reference {{reference: string {{ value: 'Questionnaire/{}'}}}}""".format(clean_name(name)), 
            '')
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
        write_library_docs(library.title,list_inputs )
        return  library

def write_library_docs(name,list_inputs ):
    buffer = get_doc_table('Inputs','required for the execution', list_inputs.values())
    #if len(buffer)>0:
    write_docs(buffer, "Library"+name.capitalize())

def get_lib_parameters_list(df_in, type = "pd"):
    
    parameters = []
    df = filter_df(df_in,type)

    
    for index, row in df.iterrows():
        if type in  ('q','c','r'):
            q_type = get_question_fhir_data_type(row['type'])
        else:
            q_type = 'boolean'
        name = row['id'] if 'id' in row else index
        if name is not None and pd.notna(name) and  name not in METADATA_CODES:
            parameters.append({'name': name, 'type':q_type, 'use': 'out'})
            desc =get_description(row)
            if desc is not None:
                desc = desc.replace(u'\xa0', u' ').replace('  ',' ')
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
            name = param["name"] ,
            type = get_lib_type(param["type"])
        ))

    if len(parameters)>0:
        return parameters
    
def filter_df(df_in,type):    
    if type == 'pd':
        df = df_in[df_in.parentId != "{{library}}"]
    elif type in ('q','c','r'):
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



def convert_reference_to_cql(cql_exp, df, list_inputs):
    # find "([^"]+)" *= *"([^"]+)" 
    valueset_linkid = [x  for x in  get_used_valueset().keys()]
    valueset_label = [x  for x in  get_used_valueset().values()]
    obs_valueset_linkid = [x  for x in get_used_obs_valueset().keys()]
    obs_valueset_label = [x  for x in get_used_obs_valueset().values()]
    obs_linkid = [x  for x in get_used_obs().keys()]
    obs_label = [x for x in get_used_obs().values()]
    changed = []
    matches = re.findall(r'([ ~!=<>voc\.]+)?"(\w[^"]+)"',cql_exp)
    out = cql_exp
    out = out.replace('HasCond', 'pfsdc.HasCond')
    out = out.replace('HasObs', 'pfsdc.HasObs')
    out = out.replace('GetObsValue', 'pfsdc.GetObsValue')


    for matching in matches:
        prefix = matching[0][-1] if len(matching[0])>0  else ''
        if prefix != '.':
            operator = bool(re.search('[~!=<>]', matching[0]))
            match = matching[1]

            if match not in changed:
                if df is not None and (bool(re.search('[^a-zA-Z]', prefix)) or prefix == '') and  len(df[(df.id == match) | ('label' in df and df.label == match)]):
                    # Localy define variable should NOT be converted but put in lower case
                    out = out.replace('"{}"'.format(match), '"{}"'.format(match) )
                elif match  in ("Yes"):
                    out = out.replace('"{}"'.format(match), 'true'.format(match) )
                    changed.append(match)
                elif match  in ("No"):
                    out = out.replace('"{}"'.format(match), 'false'.format(match) )
                    changed.append(match)
                # for valueset  converted in obs
                elif match in obs_valueset_linkid and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), GETOBS_FORMAT.format(match) )
                elif match in obs_valueset_label and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    linkid = list(get_used_obs_valueset().keys())[list(obs_valueset_label).index(match)]
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), GETOBS_FORMAT.format(linkid) )
                # for valueset
                elif match in valueset_linkid and (prefix == 'v' or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), VAL_FORMAT.format(get_used_valueset()[match]) )
                elif match in valueset_label and (prefix == 'v'   or (prefix != 'o'  and operator == True)):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'v' else '',match), VAL_FORMAT.format(match) )
                # for obs
                elif match in obs_linkid and prefix in ('',' ','o'):
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'o' else '',match), GETOBS_FORMAT.format(match) )
                    list_inputs[match]=get_input('Observation',match,'boolean/quantity',get_used_obs()[match])
                elif match in obs_label and prefix in ('',' ','o'):
                    linkid = list(get_used_obs().keys())[list(obs_label).index(match)]
                    changed.append(match)
                    out = out.replace('{0}"{1}"'.format(prefix if prefix == 'o' else '',match), GETOBS_FORMAT.format(linkid) )
                    list_inputs[linkid]=get_input('Observation',linkid,'boolean/quantity',match)
                else:
                    logger.warning("string not translated {} {} ".format(prefix,match))
                    
    # quick fix remove the select multiple
    #matches = re.findall(r"(Base\.GetObsValue\('([^']+)'\) *= *Base\.GetObsValue\('([^']+)'\))",out)
    
    matches = re.findall(r"({0} *= *{0})".format(re.escape(GETOBS_FORMAT).replace("\{\}",'([^"]+)')),out)
    
    for match in matches:
        newid='{}&{}'.format(match[1],match[2])
        replacement = (GETOBS_FORMAT + " = true").format(newid)
        logger.debug('rework {}-{} is an observation (present) '.format(match[2],get_used_obs()[match[2]] ))
        out = out.replace( match[0], replacement)
        desc = ''
        if match[1] in list_inputs:
            desc = list_inputs[match[1]]['description']
            del list_inputs[match[1]]
        if match[2] in list_inputs:
            desc += ":" + list_inputs[match[2]]['description']
            del list_inputs[match[2]]
        
 
        list_inputs[newid]=get_input('Observation',newid,'boolean/quantity',desc)
    # quick fix remove the select multiple
    matches = re.findall(r"({0} *!= *{0})".format(re.escape(GETOBS_FORMAT).replace("\{\}",'([^"]+)')),out)
    for match in matches:
        newid='{}&{}'.format(match[1],match[2])
        replacement = (GETOBS_FORMAT + " = false").format(newid)
        logger.debug('rework {}-{} is an observation (absent)'.format(match[2],get_used_obs()[match[2]] ))
        out = out.replace( match[0], replacement)
        desc = ''
        if match[1] in list_inputs:
            desc = list_inputs[match[1]]['description']
            del list_inputs[match[1]]
        if match[2] in list_inputs:
            desc += ":" + list_inputs[match[2]]['description']
            del list_inputs[match[2]]
        list_inputs[newid]=get_input('Observation',newid,'boolean/quantity',desc)
    # Base.GetObsValue('EmCare.B15S2.DE09') = val."some mucous membrane pallor"
    matches = re.findall(r"({0} *= *{1})".format(re.escape(GETOBS_FORMAT).replace("\{\}","([^']+)"),re.escape(VAL_FORMAT).replace("\{\}","([^']+)")),out)

    #matches = re.findall(r"(Base\.GetObsValue\('([^']+)'\) *= *val\.\"([^\"]+)\")",out)
    for match in matches:
        linkid = list(get_used_valueset().keys())[list(valueset_label).index(match[2])]
        replacement = GETOBSCODE_FORMAT.format(match[1],linkid)
        logger.debug('rework {0} = val."{1}" to  GetObsValueCode("{0}, "{2}")'.format(match[1],match[2],linkid ))
        #out = out.replace( match[0], replacement)
        x
        list_inputs[match[1]]['valueType'] = 'CodeableConcept'
    # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(((?:[a-zA-Z][a-zA-Z'\(\)_\.]+)?(?:\"[^\"]+\")?) *!= *true)",out)
    for match in matches:
        replacement = "Coalesce({},false)!=true".format(match[1])
        logger.debug('rework {0} != true to  Coalesce({0},false)!=true'.format(match[1]))
        out = out.replace( match[0], replacement)
        # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(ToInteger\(((?: *(?:[a-zA-Z]+\.)?\"[^\"]+\" *[~=<>!]+ *(?:(?:[a-zA-Z]+\.)?(?:\"[^\"]+\")|[a-z]+) *(?:or|and)?)+)\))",out)
    for match in matches:
        replacement = "ToInteger(Coalesce({},false))".format(match[1])
        logger.debug('rework {0}  to  {1}'.format(match[0],replacement))
        out = out.replace( match[0], replacement)    
    matches = re.findall(r"= val\.",out)
    
    # ~ required to test code against codeableconcept
    for match in matches:
        replacement = "~ val."
        logger.debug('rework = val to ~ val')
        out = out.replace( match, replacement)
    return out

def get_input(profile,code,valueType,desc=''):
    return {
            'type' : profile,
            'code' : code,
            'valueType' : valueType,
            'description': desc
        }

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

def get_cql_raw_action(id, row, expression_column, df ):
    cql_exp_raw = row[expression_column] if row[expression_column].strip() != '{{cql}}' else ''
    # to create the reverse rule
    sub =  get_additionnal_cql(id,df,expression_column)
    if len(sub)>0 and cql_exp_raw != '':
        cql_exp_raw =reindent("({})\n and ({})\n".format(cql_exp_raw,sub),4)
    elif len(sub)>0:
        cql_exp_raw =reindent("{}\n".format(sub),4)
    elif cql_exp_raw == '':
        logger.debug('no CQL found {}'.format(id))
    # translation to CQL function
    return  cql_exp_raw

def get_intputs_docs( df_questions_item):
    pass

def get_description(row):
    if 'label' in row and pd.notna(row['label']):
        return row['label']
    elif 'description' in row and pd.notna(row['description']):
        row['description']
    else:
        return None

def write_action_condition(action):
    cql = ""
    if action.description is not None:
        for condition in action.condition:
            
            ## Output false, manual process to convert the pseudo-code to CQL
            cql += "/*\n \"{0}\":\n ".format(condition.expression.description if condition.expression.description is not None else action.description)+"\n */\n "+\
                "define \"{0}\":\n ".format(str(condition.expression.expression).replace("\n", ""))+ \
                    "  false" + "\n\n "
    return cql    

def format_cql_df(library, df_actions,  type):
    cql = {}
    libs = [{
                'name':"pyfhirsdc",
                'version': __version__,
                'alias':"pfsdc"
            },{
                'name':get_processor_cfg().scope.lower()+"valueset",
                'version':get_fhir_cfg().lib_version,
                'alias':"val"
            }]
#{
#                'name':get_processor_cfg().scope.lower()+"base",
#                'version':get_fhir_cfg().lib_version,
#                'alias':"Base"
#            },        
    i = 0
    oi = i
    list_inputs = {}
    df_main = df_actions.dropna(axis=0, subset='id')
    if len(df_actions)>0:
        
        for index, row in df_main.iterrows():
            ref = row['id'] if 'id' in row else index 
            
            desc = get_description(row)
            if index == "{{library}}" or "id" in row and pd.notna(row['id']) and row['id'] == "{{library}}":
                if desc is not None:
                    details =  desc.split("::")
                    name = get_pyfhirsdc_lib_name(details[0])
                    version = details[2] if len(details)>2 else None
                    alias = details[1] if len(details)>1 else None
                    libs.append({
                        'name':name,
                        'version':version,
                        'alias':alias
                    })
                else:
                    logger.error(f"Libray reference for {library.id} not set properly, should be in label with the format lib_id::alias::lib_version")
            # PlanDefinition CQL
            # applicability -> "id" : cql
            # start -> "start::id" : cql
            # end -> "end::id" : cql
            # write_cql_action(name,desc, cql_exp, prefix,display=None
            if 'stopExpressions' in row and pd.notna(row['stopExpressions']):
                cql[i] = get_cql_define(ref, row,'stopExpressions', df_actions,list_inputs)
                i += 1
            if 'startExpressions' in row and pd.notna(row['startExpressions']):
                cql[i] = get_cql_define(ref, row,'startExpressions', df_actions,list_inputs)
                i += 1
            if 'applicabilityExpressions' in row and pd.notna(row['applicabilityExpressions']):
                cql[i] = get_cql_define(ref, row,'applicabilityExpressions', df_actions,list_inputs)
                i += 1
                # add the wrapper name -> id
                if pd.notna(desc):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['applicabilityExpressions']['prefix'], desc,ref)
                    i += 1
            ## questionnaire initial expression in CQL, FIXMDe
            if 'initialExpression' in row and pd.notna(row['initialExpression']) and not re.match("^(uuid)\(\)$",row['initialExpression'].strip()) and row['type'] != '{{cql}}' :
                cql[i] = get_cql_define(ref, row,'initialExpression',df_actions,list_inputs)
                i += 1
                if pd.notna(row['label']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['initialExpression']['prefix'], row['label'],ref)
                    i += 1
            if type == 'c' and 'enableWhenExpression' in row and pd.notna(row['enableWhenExpression']):
                cql[i] = get_cql_define(ref, row,'enableWhenExpression',df_actions,list_inputs)
                i += 1
                if pd.notna(row['label']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['enableWhenExpression']['prefix'], row['label'],ref)
                    i += 1
                cql,i = get_postcoordinations_cql(row, cql,i,df_actions,list_inputs)
            while  i > oi :
                cql[oi] = inject_config(cql[oi])
                oi+=1

    if  any([l['type'] == "Observation" for l in list_inputs.values()]):
        libs.append(    {
                'name':get_processor_cfg().scope.lower()+"observation",
                'version':get_fhir_cfg().lib_version,
                'alias':"obs"
            })
    
    cql['header'] = writeLibraryHeader(library, libs)
    cql['header'] += writeGetObs(list_inputs)
    return cql, list_inputs

def get_postcoordinations_cql(row, cql,i,df_actions,list_inputs):

    postcoordinations = df_actions[(df_actions['parentId'] == row['id']) & (df_actions['type'] == 'postcoordination')]['id'].tolist()
    if len(postcoordinations) > 0:  
        cql_exp_raw = '|'.join(get_postcoordination_cql(postcoordinations))
        cql_exp = convert_reference_to_cql(cql_exp_raw,df_actions, list_inputs)
        cql[i] = write_cql_action(row['id'],cql_exp_raw, cql_exp, 'getPostCordination_',display=None)
        i+=1
    
    return cql,i

def get_postcoordination_cql(postcoordinations):
    cql= []
    for postcoordination in postcoordinations:
        
        cql.append( f"""
if "{postcoordination}" then {{ Extension {{
    url : uri {{value: '{get_fhir_cfg().canonicalBase + 'StructureDefinition/postcoordination'}'}},
    value: FHIR.CodeableConcept {{coding: {{ FHIR.Coding {{ system: FHIR.uri {{ value : '{get_custom_codesystem_url()}' }}, code: FHIR.code {{value: '{postcoordination}' }} }} }} }}
}} }}
else null
        """)
    return cql


def writeGetObs(list_inputs):
    ret = ""
    for input in list_inputs.values():
        if input['type'] == "Observation":
            ret += write_cql_action(GETOBS_FORMAT.format(input['code'])[1:-1],'', GETOBSVALUE_FORMAT.format(input['code']), '',input['description'] if 'description'in input else '')
    return ret




def get_cql_define(name, row, expression_column, df_actions, list_inputs):
    prefix = ROW_EXPRESSIONS[expression_column]['prefix']
    cql_exp_raw = get_cql_raw_action(row['id'], row, expression_column, df_actions )
    if cql_exp_raw != '':
        cql_exp = convert_reference_to_cql(cql_exp_raw,df_actions, list_inputs)
        return write_cql_action(name,cql_exp_raw, cql_exp, prefix,display=None) 
    else:
        return ''

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

def check_expression_keyword(row, keyword):
    for name, exp in ROW_EXPRESSIONS.items():
        if name in row and pd.notna(row[name]) and keyword in str(row[name]):
            return True
    