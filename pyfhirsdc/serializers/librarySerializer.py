### Function that creates the constant part of cql files 
import logging
import os

import pandas as pd
from fhir.resources.R4B.identifier import Identifier

from pyfhirsdc.config import append_used_obs, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.utils import get_custom_codesystem_url
from pyfhirsdc.converters.valueSetConverter import add_concept_in_valueset_df
from pyfhirsdc.serializers.utils import reindent

logger = logging.getLogger("default")

def getIdentifierFirstRep(planDef):
    if (not planDef.identifier):
        identifier = Identifier.construct()
        planDef.identifier = [identifier]
    return planDef.identifier[0]  


GETOBSVALUE_FORMAT = "pfsdc.GetObsValue('{0}')"
GETOBS_FORMAT = '"OBSdefine.{}"'
GETOBSCODE_FORMAT = "pfsdc.HasObsValueCode('{}', '{}')"
VAL_FORMAT='val."{0}"'


    
# libs [{name,version,alias}]
# parameters [{name,type}]
def writeLibraryHeader(library, libs = [], other_header='context Patient'):
    return f"""/*
@author: {get_processor_cfg().author}
@description: This library is part of the project {get_processor_cfg().scope}
*/
library {library.name} version '{get_fhir_cfg().lib_version}'
using FHIR version '{get_fhir_cfg().version}'
include FHIRHelpers version '{get_fhir_cfg().version}' called FHIRHelpers 
{get_include_lib(libs, library)}

parameter "canonical_base" String default '{get_fhir_cfg().canonicalBase}'
parameter "custom_code_system" String default '{get_custom_codesystem_url()}' 
{get_include_parameters(library.parameter)}

{other_header}

"""

# libs is a list {name='', version='', alias = ''}
def get_include_lib(libs, library = None):
    ret = ''
    for lib in libs:
        if 'name' in lib and lib['name'] is not None and len(lib['name'])>0:
            ret+="include {}".format(lib['name'])
            if 'version' in lib and lib['version'] is not None and len(lib['version'])>0:
               ret+=" version '{}'".format(lib['version'].replace("{{LIB_VERSION}}",get_fhir_cfg().lib_version).replace("{{FHIR_VERSION}}",get_fhir_cfg().version))
            else:
                logger.error(" version missing for {} but mandatory as dependency for library {}".format(lib['name'], library.name))
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
        

def get_code_cql_from_concepts(concepts, lib, add_to_valueset,low_case = False):
    # write 3 cql : start, end, applicability
    list_of_display = []
    cql = {}
    libs = []
    cql['header'] = writeLibraryHeader(lib, libs, 
        'codesystem "{}" : \'{}\'\n'.format(get_processor_cfg().scope, get_custom_codesystem_url()) )
    i = 0
    if concepts is not None:
        for concept in concepts:
            concept.display=str(concept.display)
            if concept.display not in list_of_display:
                list_of_display.append(concept.display)
                if (concept is not None and concept.code is not None):       
                    concept_cql = write_code(concept)
 
                        
                    #concept_cql = write_obsevation(concept)
                    if concept_cql is not None:
                        if add_to_valueset:
                            add_concept_in_valueset_df(lib.name, concepts)
                        else:
                            append_used_obs(concept.code, concept.display)
                        cql[i] = concept_cql
                        i = i+1
                        if low_case:
                            concept_lc = concept.copy()
                            concept_lc.display = concept_lc.display.lower()
                            cql[i] = write_code(concept_lc)
                            i = i+1
            
            elif any([ c.display == concept.display and  c.code != concept.code for c in concepts]):
                logger.warning("{} :{} is defined multiple times with different id than {}".format(lib.name,concept.display, concept.code))
                
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
            "define \"{0}\":\n".format(str(concept.display).replace("\n", ""))+ \
                "  B.HasObs('{}')".format(concept.code,get_custom_codesystem_url()) + "\n\n"
    if concept.code is not None and concept.code:
        ## Output false, manual process to convert the pseudo-code to CQL    
        cql += "define \"{0}\":\n".format(str(concept.code).replace("\n", ""))+ \
                "  B.HasObs('{}')".format(concept.code, get_custom_codesystem_url()) + "\n\n"
    return cql    

def write_code(concept):
    cql = ""
    if concept.display is not None and pd.notna(concept.display):
        ## Output false, manual process to convert the pseudo-code to CQL
        cql += "code \"{0}\": '{1}' from \"{2}\" display '{3}'\n".format(concept.display.replace('"', '\\"'),concept.code, get_processor_cfg().scope  ,concept.display.replace("'", "\\'"))
        
        return cql
    

"""
docs are list of this structure
{
    'type' : profile,
    'code' : id or path,
    'valueType' :data type,
    'description': decription
}
"""
    
      




def write_cql_action(name,desc, cql_exp, prefix=None,display=None):

    ret =   """
/* 
{1}{2} : {0}
{3}
*/
define "{1}{2}":
{4}
""".format(
    (str(display).replace("\n", "") if display is not None else '') , 
    (str(prefix).replace("\n", "") if prefix is not None else '') , 
    name,
    desc,
    reindent(cql_exp,4)
    )
    return ret


def write_cql_alias(prefix, alias,reference):
    return write_cql_action(alias,"Alias", '"'+reference+'"', prefix,reference)

