### Function that creates the constant part of cql files 
import logging
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

from pyfhirsdc.config import (get_defaut_path, get_fhir_cfg, get_processor_cfg,
                              get_used_obs, get_used_obs_valueset,
                              get_used_valueset)
from pyfhirsdc.converters.extensionsConverter import add_library_extensions
from pyfhirsdc.converters.questionnaireItemConverter import \
    get_question_fhir_data_type
from pyfhirsdc.converters.utils import (clean_group_name, clean_name,
                                        get_codableconcept_code,
                                        get_resource_url, inject_config)
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
    'id':{'col':'description', 'prefix':'', 'kind':''}
    
}


def generate_attached_library(resource, df_actions, type = 'pd'):
    library = generate_library(resource.name, df_actions, type)
    if library is not None:
        libraryCanonical = Canonical(library.url+"|"+get_fhir_cfg().lib_version)
        if hasattr(resource, 'library') and resource.library is None: 
            resource.library = []    
            resource.library.append(libraryCanonical)
        else:
            resource = add_library_extensions(resource, library.id)
        return True
        
def generate_library(name, df_actions, type = 'pd', description = None):

    id = clean_name(name)
    logger.info("Generating library " + name + ".......")
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
    
    cql, list_inputs =format_cql_df(library, df_actions, type)
    if type == 'q':
        cql['backref'] = write_cql_action(
            'BackReference',
            'back reference to resource', 
            """Reference {{reference: string {{ value: 'Questionnaire/{}'}}}}""".format(name), 
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



def convert_reference_to_cql(cql_exp, df, list_inputs):
    # find "([^"]+)" *= *"([^"]+)" 
    valueset_linkid = [x  for x in  get_used_valueset().keys()]
    valueset_label = [x  for x in  get_used_valueset().values()]
    obs_valueset_linkid = [x  for x in get_used_obs_valueset().keys()]
    obs_valueset_label = [x  for x in get_used_obs_valueset().values()]
    obs_linkid = [x  for x in get_used_obs().keys()]
    obs_label = [x for x in get_used_obs().values()]
    changed = []
    matches = re.findall(r'([ !=<>voc\.]+)?"(\w[^"\.]+)"',cql_exp)
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
                    out = out.replace('"{}"'.format(match), '"{}"'.format(match) )
                elif match  in ("Yes"):
                    out = out.replace('"{}"'.format(match), 'true'.format(match) )
                    changed.append(match)
                elif match  in ("No"):
                    out = out.replace('"{}"'.format(match), 'false'.format(match) )
                    changed.append(match)
                # for valueset attached converted in obs
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
        
        list_inputs[match[1]]['valueType'] = 'CodeableConcept'
    # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(((?:[a-zA-Z][a-zA-Z'\(\)_\.]+)?(?:\"[^\"]+\")?) *!= *true)",out)
    for match in matches:
        replacement = "Coalesce({},false)!=true".format(match[1])
        logger.debug('rework {0} != true to  Coalesce({0},false)!=true'.format(match[1]))
        out = out.replace( match[0], replacement)
        # support "dsfsdfs" !=true or Base.ASDFwsed('code')!=true
    matches = re.findall(r"(ToInteger\( *((?:[a-zA-Z'_\.]+(\([^\)]+\))?|\"[^\"]+\")[^\)=!<>]*)\))",out)
    for match in matches:
        replacement = "ToInteger(Coalesce({},false))".format(match[1])
        logger.debug('rework {0}  to  {1}'.format(match[0],replacement))
        out = out.replace( match[0], replacement)
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
    list_inputs = {}
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
                if pd.notna(row['description']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['applicabilityExpressions']['prefix'], row['description'],ref)
                    i += 1
            ## questionnaire initial expression in CQL, FIXMDe
            if 'initialExpression' in row and pd.notna(row['initialExpression']) and not re.match("^(uuid)\(\)$",row['initialExpression'].strip()) and row['type'] != '{{cql}}' :
                cql[i] = get_cql_define(ref, row,'initialExpression',df_actions,list_inputs)
                i += 1
                if pd.notna(row['label']):
                    cql[i] = write_cql_alias(ROW_EXPRESSIONS['initialExpression']['prefix'], row['label'],ref)
                    i += 1
            while  i > oi :
                cql[oi] = inject_config(cql[oi])
                oi+=1

    
    cql['header'] = writeLibraryHeader(library, libs)
    cql['header'] += writeGetObs(list_inputs)
    return cql, list_inputs

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

def check_expression_keyword(row, keword):
    for name, exp in ROW_EXPRESSIONS.items():
        if name in row and pd.notna(row[name]) and keword in row[name]:
            return True
    