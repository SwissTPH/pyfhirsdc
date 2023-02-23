import logging
import re
from importlib.resources import path

import pandas as pd
import validators
from fhir.resources.elementdefinition import (ElementDefinition, ElementDefinitionBinding,
                                              ElementDefinitionType,)
from fhir.resources.fhirtypes import (Code, Id, StructureDefinitionContextType, Uri, Canonical)

from fhir.resources.structuredefinition import (
    StructureDefinition, StructureDefinitionDifferential)

from pyfhirsdc.config import get_dict_df, get_fhir_cfg
from pyfhirsdc.converters.mappingConverter import get_base_profile
from pyfhirsdc.converters.questionnaireItemConverter import (
    get_display, get_question_fhir_data_type)
from pyfhirsdc.converters.utils import (clean_name, get_resource_name,
                                        get_resource_url)

logger = logging.getLogger("default")

Id.configure_constraints(regex=re.compile(r"^[A-Za-z0-9\-\.]+(\[x\](\.[a-zA-Z]+)?)?(:[A-Za-z0-9\-.]+(\[x\](\.[a-zA-Z]+)?)?)?$"))      
Id.configure_constraints(max_length=128)      

def init_extension_def(element):
    map_extension = element['map_extension'].split('::')[0].strip()
    ## Check for the map resource of the extension and grab the extension URL
    ## Replace the Canonical base URL placeholder with the real url 
    
    if not validators.url(map_extension):
        id = clean_name(map_extension)
        extension_name = get_resource_name("StructureDefinition", id)
        extension_url = get_resource_url("StructureDefinition", id)
        # Pydantics does not allow to add a property to an object without providing all the 
        # mandatory fields. So first this object has to be created 
        logger.info(extension_name)
        structure_def = StructureDefinition(
            kind = Code('complex-type'),
            abstract = False,
            name = extension_name,
            status = Code('draft'), 
            type = "Extension",
            url = Uri(extension_url).strip(),
            id = id,
            experimental = False,
            version = get_fhir_cfg().version,
            baseDefinition = "http://hl7.org/fhir/StructureDefinition/Extension",
            derivation = "specialization"
        )
        if pd.notna(element['description']):
            structure_def.description = element['description']
        if pd.notna(element["map_profile"]):
            structure_def.context = [StructureDefinitionContextType({"type": "element",\
                "expression": '-'.join(element['map_profile'].split(' ',1)[1:])})]
        min_cardinality = element['map_extension'].split('::')[1].strip()
        max_cardinality = element['map_extension'].split('::')[2].strip()
        element_type = get_question_fhir_data_type(element['type'])
        if element_type is None:
            logger.error("an extension mapping is with a not compatible questiontype" + element['type'])
        add_reference = False
        if element_type == 'choice':
            element_valueset_name = element['type'].split(' ',1)[-1]
            ## Check if the name after slelect_one starts with a capital or not.
            ## if it starts with a capital it is a reference to a profile
            logger.debug("name of the value set: " +element_valueset_name)
            if element_valueset_name[0].isupper():
                add_reference = True
                element_type = 'Reference'
            else:
                element_type = 'CodeableConcept'
                add_binding = True
        valuePath = "Extension.value{}"
        extension_element = [ElementDefinition(
                id ="Extension",
                path = "Extension",
                short = extension_name,
                definition = element['description'],
                min = min_cardinality,
                max = max_cardinality
            ),
            ElementDefinition(
                id = "Extension.extension",
                path = "Extension.extension",
                min = min_cardinality,
                max = max_cardinality
            ),
            ElementDefinition(
                id = "Extension.url",
                path = "Extension.url",
                fixedUri = Uri(extension_url),
            ), 
            ElementDefinition(
                id =  "Extension.value",
                path =  "Extension.value" + element_type.capitalize(),
                short = extension_name,
                definition = element['description'],
                min = min_cardinality,
                max = max_cardinality
            )
        ]

        element_def_type = ElementDefinitionType.construct()
        element_def_type.code = get_question_fhir_data_type(element_type)
        if add_reference == True : 
            element_def_type.targetProfile = [get_fhir_cfg().canonicalBase+\
                    'StructureDefinition/'+element['definition']+'-'+element_valueset_name]
        extension_element[-1].type = [element_def_type]
        differential = StructureDefinitionDifferential.construct()
        differential.element = extension_element
        structure_def.differential = differential
        return structure_def
    return None

def convert_df_to_profiles():
    profiles = []
    names = []
    q_idx = []
    dfs_questionnaire = get_dict_df()['questionnaires']
    all_questionnaires = pd.concat(dfs_questionnaire, ignore_index=True)
    # get the valid line from the profile tabs,  profile and extensions
    df_profile_ext  = get_dict_df()['profile'].dropna(axis=0, subset=['id'])
    # get only the line witout "profile" meaning it is the main line for the profile
    df_profile = df_profile_ext[pd.isna(df_profile_ext.profile)]
    
    all_questionnaires.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id')
    #Grouping rows based on the profiles, so that we can go through the different groups and create
    # the corresponding profiles with the right attributes

    
    #for key, item in grouped_profiles:
    #    logger.info("Profile: ", key)
    #    logger.info(grouped_profiles.get_group(key), "\n\n")
    for idx, row in df_profile.iterrows():
        profile = init_profile_def(row)
        names.append(profile.name)
        # get the df for the profile extension
        df_extensions = df_profile_ext[df_profile_ext.profile == profile.id]
        profile = extend_profile(profile, df_extensions )
        profiles.append(profile)
    return profiles,names

def init_profile_def(row):
    profile_id = clean_name(row['id'])
    #TODO USE STD BASED DEFINITION IF NONE IS DEFIEND IN EXCEL
    structure_def= StructureDefinition(
        id = profile_id,
        kind = Code('resource'),
        title = row['title'],
        name = row['title'],
        abstract = False,
        status = Code('active'),
        type = get_base_profile(row['title']),
        url = get_resource_url('StructureDefinition', Id(profile_id)),
        baseDefinition = Uri(row['baseProfile']),
        derivation = "specialization",
        experimental = False,
        fhirVersion = get_fhir_cfg().version,
        description = row['description'] if pd.notna(row['description']) else None
    )
    return structure_def

def get_extension_binding(row):
    if pd.notna(row.type) and row.type == "CodeableConcept":
        if pd.notna(row.value):
            return ElementDefinitionBinding(strength="required", valueSet=Canonical(get_resource_url("ValueSet", row.value)))
        else: logger.error("Mising value for Extension %s with CodableConcept type", row.id)

def get_extension_profile(row):
    if pd.notna(row.type) and row.type == "Reference":
        if pd.notna(row.value):
            return [get_resource_url('StructureDefinition', Id(row['value'])),]
        else: logger.error("Mising value for Extension %s with Reference type", row.id)
    
def extend_profile(profile, df_extensions):
    differential_elements = []

    for idx, row in df_extensions.iterrows():
        logger.info("extending profiles")

        extension_def = ElementDefinition(
            id = row['map_path'] + ':' + row['id'],
            short = row['id'],
            path = row['map_path'] if pd.notna(row['map_path']) else '',
            min = row['cardinality'].split('::')[0].strip(),
            max = row['cardinality'].split('::')[1].strip(),
            type = [ElementDefinitionType(
               code = row['type'] if pd.notna(row.type) else "Extension",
               profile = get_extension_profile(row)
            )],
            binding= get_extension_binding(row) 
        )        
        differential_elements.append(extension_def)
        
        if len(differential_elements) > 0:
            profile.differential = StructureDefinitionDifferential(
                element= differential_elements
            )
    return profile