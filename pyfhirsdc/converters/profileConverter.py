import logging
import re
from importlib.resources import path

import pandas as pd
import validators
from fhir.resources.R4B.elementdefinition import (ElementDefinition,
                                              ElementDefinitionBinding,
                                              ElementDefinitionType)
from fhir.resources.R4B.fhirtypes import (Canonical, Code, Id,
                                      StructureDefinitionContextType, Uri)
from fhir.resources.R4B.structuredefinition import (
    StructureDefinition, StructureDefinitionDifferential)

from pyfhirsdc.config import get_dict_df, get_fhir_cfg
from pyfhirsdc.converters.questionnaireItemConverter import (
    get_display, get_question_fhir_data_type)
from pyfhirsdc.converters.utils import (clean_name, get_resource_name, get_exact_match_profile,
                                        get_resource_url, get_base_profile, FHIR_BASE_PROFILES)

logger = logging.getLogger("default")

Id.configure_constraints(regex=re.compile(r"^[A-Za-z0-9\-\.]+(\[x\](\.[a-zA-Z]+)?)?(:[A-Za-z0-9\-.]+(\[x\](\.[a-zA-Z]+)?)?)?$"))      
Id.configure_constraints(max_length=128)      


def get_extension_diferential(name, desc, ext_type, ext_url, value):
    element_defenitions = [ElementDefinition(
                id = "Extension",
                path = "Extension",
                short = name,
                definition = desc,
                min = 1,
                max = 1
            ),
            ElementDefinition(
                id = "Extension.extension",
                path = "Extension.extension",
                min = 1,
                max = 1
            ),
            ElementDefinition(
                id = "Extension.url",
                path = "Extension.url",
                fixedUri = Uri(ext_url),
            ), 
        ]

    if (ext_type.lower() == "reference"):
        element_defenitions.append(
            ElementDefinition(
            id =  "Extension.value",
            path =  "Extension.value" + ext_type[0].capitalize()+ext_type[1:],
            short = name,
            definition = desc,
            type = [ElementDefinitionType(
                code = ext_type,
                targetProfile = [value]
            )],
            binding = get_extension_binding(ext_type , value) ,
            min = 1,
            max = 1
        ))
    else:
        element_defenitions.append(
            ElementDefinition(
            id =  "Extension.value",
            path =  "Extension.value" + ext_type[0].capitalize()+ext_type[1:],
            short = name,
            definition = desc,
            type = [ElementDefinitionType(
                code = ext_type,
            )],
            binding = get_extension_binding(ext_type , value) ,
            min = 1,
            max = 1
        ))
    return element_defenitions

def convert_df_to_profiles():
    profiles = []
    names = []
    q_idx = []
    dfs_questionnaire = get_dict_df()['questionnaires']
    all_questionnaires = pd.concat(dfs_questionnaire, ignore_index=True)
    # get the valid line from the profile tabs,  profile and extensions
    if "profile" in get_dict_df():
        df_profile_all  = get_dict_df()['profile'].dropna(axis=0, subset=['id'])
        # get only the line witout "profile" meaning it is the main line for the profile
        df_profile = df_profile_all[df_profile_all.definitionType == 'resource']
        
        df_profile_ext  = df_profile_all[df_profile_all.definitionType == 'Extension']
        df_profile_elements = df_profile_all[df_profile_all.definitionType == 'element']
 
        #Grouping rows based on the profiles, so that we can go through the different groups and create
        # the corresponding profiles with the right attributes

        
        #for key, item in grouped_profiles:
        #    logger.info("Profile: ", key)
        #    logger.info(grouped_profiles.get_group(key), "\n\n")
        for idx, row in df_profile.iterrows():
            profile = init_profile_def(row)
        
            # get the df for the profile extension
            df_extensions = df_profile_ext[df_profile_ext.profile == profile.id]
            profile = extend_profile(profile, df_extensions, df_profile_elements )
            profiles.append(profile)

        for idx, row in df_profile_ext.iterrows():
            profile = init_profile_def(row)
            profile_id = clean_name(row['id'])
            profile.differential = StructureDefinitionDifferential(
                element= get_extension_diferential(
                    row.id, 
                    row.description, 
                    row.type, 
                    get_resource_url('StructureDefinition', Id(profile_id)),
                    row.value)
            )
            profiles.append(profile)
            
        # check if there is misssing profiles    
        all_questionnaires = all_questionnaires.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id')
        for idx, row in all_questionnaires.iterrows():
            #TODO exclude std resource
            profile_type = row.map_profile.strip()
            found = profile_type in FHIR_BASE_PROFILES
            if not found:
                for profile in profiles:
                    if  profile_type in (profile.id, profile.title ):
                        found = True                                                                                                               
                        break
            if not found:
                logger.warning('Profile not found for %s', row.map_profile)

        return profiles

def init_profile_def(row):
    is_extension_definition = pd.notna(row.definitionType) and row.definitionType == 'Extension'
    profile_id = clean_name(row['id'])
    #TODO USE STD BASED DEFINITION IF NONE IS DEFIEND IN EXCEL
    structure_def= StructureDefinition(
        id = profile_id,
        kind = Code('complex-type') if is_extension_definition else Code('resource'),
        title = row['title'],
        name = row['title'],
        abstract = False,
        status = Code('active'),
        type = 'Extension' if is_extension_definition else get_exact_match_profile(row['title']),
        context = get_context(get_base_profile(row.profile)) if is_extension_definition else None,
        url = get_resource_url('StructureDefinition', Id(profile_id)),
        baseDefinition = Uri('http://hl7.org/fhir/StructureDefinition/Extension')  if  is_extension_definition else  Uri(row['baseProfile']),
        # derivation = "constraint" if is_extension_definition else  "specialization",
        derivation = "constraint", #set to be complient with R5
        experimental = False,
        fhirVersion = get_fhir_cfg().version,
        description = row['description'] if pd.notna(row['description']) else None
    )
    return structure_def

def get_context(base_profile):
    return [StructureDefinitionContextType({"type": "element",\
                "expression":base_profile })]

def get_extension_binding(type , value):
    if type == "CodeableConcept":
        if pd.notna(value):
            return ElementDefinitionBinding(strength="required", valueSet=Canonical(get_resource_url("ValueSet", value)))
        else: logger.error("Missing value for Extension %s:%s with CodableConcept type", type , value)

    
def extend_profile(profile, df_extensions, df_elements):
    # base_profile = get_base_profile(profile.id)
    base_profile = get_exact_match_profile(profile.id)
    # first diferential element of a resource must be this simple element
    differential_elements = [ElementDefinition(
        id = base_profile,
        path = base_profile
    )]
    logger.debug("extending profile %s", profile.id)
    for idx, row in df_extensions.iterrows():
        logger.debug("adding %s to profile %s", row.id, profile.id)
        extension_def = init_extension_definition(row)
        differential_elements.append(extension_def)

    for idx, row in df_elements.iterrows():
        if row['id'].lower() != profile.id.lower():
            break
        elements = init_element_defenition(row)
        differential_elements.append(elements)

    if len(differential_elements) > 0:
        differential_elements = [x for x in differential_elements if x is not None]
        profile.differential = StructureDefinitionDifferential(
            element= differential_elements
        )
    return profile

def bind_cardinality(row):
    cardinality = row['cardinality'].split('::')
    if  len(cardinality) == 2 :
        if '*' in cardinality[0]:
            cardinality[0] = '*'
        else:
            cardinality[0] = int(cardinality[0])
        if '*' in cardinality[1]:
            cardinality[1] = '*'
        else:
            cardinality[1] = int(cardinality[1])
            
    else:
        cardinality = None
    
    return cardinality

def init_element_defenition(row):
    cardinality = bind_cardinality(row)
    element_split = row['element'].split("::")


    path = row['map_path'] + "." + element_split[0] if pd.notna(row['map_path']) else get_exact_match_profile(row['profile'])
    element_defenition = None
    print(element_split[0])
    #TODO: Move the element definition to a sepeare function like get_extention_differential. If neccessary
    if (row['type'] == 'CodeableConcept' and element_split[0] == 'code' and element_split[1] == 'binding'):
        element_defenition = ElementDefinition(
            id = path,
            path = path,
            min = cardinality[0] if cardinality is not None else None,
            max = cardinality[1] if cardinality is not None else None,
            binding = get_extension_binding(row['type'], row['value'])
        )
    elif (row['type'].lower() == 'reference'):
        element_defenition = ElementDefinition(
            id = path,
            path = path, 
            min = cardinality[0] if not None else None,
            max = cardinality[1] if not None else None,
            type = [ElementDefinitionType(
                code = row['type'],
                targetProfile = [get_resource_url('StructureDefinition', row['value'])]
            )]
        )
    if element_defenition is not None:
        return element_defenition
    else: 
        return None

def init_extension_definition(row):

    cardinality = bind_cardinality(row)    
    path = row['map_path'] +".extension" if  pd.notna(row['map_path']) else get_base_profile(row.id)

    return ElementDefinition(
        id = path + ':' + row['id'],
        short = row['id'],
        path = path ,
        min = cardinality[0] if cardinality is not None else None,
        max = cardinality[1] if cardinality is not None else None,
        type = [ElementDefinitionType(
            code = "Extension",
            profile = [get_resource_url('StructureDefinition', row.id)]
        )]
    )       