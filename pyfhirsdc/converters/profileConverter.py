import logging
import re
from importlib.resources import path

import pandas as pd
import validators
from fhir.resources.elementdefinition import (ElementDefinition,
                                              ElementDefinitionType)
from fhir.resources.fhirtypes import (Code, Id, StructureDefinitionContextType,
                                      Uri)
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
    map_extension = element['map_extension'].strip().split('::')
    ## Check for the map resource of the extension and grab the extension URL
    ## Replace the Canonical base URL placeholder with the real url 
    
    if not validators.url(map_extension[0]):
        id = clean_name(map_extension[0].strip())
        extension_name = get_resource_name("StructureDefinition", map_extension[0].strip())
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
            derivation = "constraint"
        )
        if pd.notna(element['description']):
            structure_def.description = element['description']
        if pd.notna(element["map_profile"]):
            structure_def.context = [StructureDefinitionContextType({"type": "element",\
                "expression": '-'.join(element['map_profile'].split(' ',1)[1:])})]
        min_cardinality = map_extension[1].strip()
        max_cardinality = map_extension[2].strip()
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

    df_profile  = get_dict_df()['profile'].dropna(axis=0, subset=['title'])
    
    all_questionnaires.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id')
    #Grouping rows based on the profiles, so that we can go through the different groups and create
    # the corresponding profiles with the right attributes

    
    #for key, item in grouped_profiles:
    #    logger.info("Profile: ", key)
    #    logger.info(grouped_profiles.get_group(key), "\n\n")
    for idx, row in df_profile.iterrows():
        profile = init_profile_def(row)
        names.append(profile.name)
        df = all_questionnaires[all_questionnaires.map_profile == profile]
        profile = extend_profile(profile, df )
        profiles.append(profile)
    return profiles,names


def init_profile_def(element):
    profile_id = clean_name(element['title'])
    
    structure_def= StructureDefinition(
        id = profile_id,
        kind= Code('complex-type'),
        title = element['title'],
        name = element['title'],
        abstract = False,
        status = Code('active'),
        type = get_base_profile(element['title']),
        url = get_resource_url('StructureDefinition', Id(profile_id)),
        baseDefinition = Uri(element['baseProfile']),
        derivation = "constraint",
        experimental = False,
        fhirVersion = get_fhir_cfg().version,
        description = element['description'] if pd.notna(element['description']) else None
    )
    

    return structure_def

def extend_profile(profile, all_questionnaires):
    resource_type = get_base_profile(profile.name)
    element_list = []
    element_list.append({
        "id": clean_name(resource_type),
        "path": resource_type
    })
    logger.info('Processing Profile: {0}'.format(profile.name))
    df_valueset = get_dict_df()['valueset']
    
    for idx, row in all_questionnaires.iterrows():
        # if there is a map_extension then we have to link it to the extension and 
        # add a slice name
        extension = row["map_extension"]
        is_profile = pd.notna(row["map_profile"])

        if not pd.notna(row["map_profile"]) and not pd.notna(row["map_path"]):
            continue
        if pd.notna(extension) and is_profile:
            if "::" in extension:
                extension_details =extension.strip().split('::')
                extension_name= extension_details[0].split('/')[-1].strip()
                extension_min =  extension_details[1].strip()
                extension_max =  extension_details[2].strip()
            else: 
                extension_min = '0'
                extension_max = '*'
                extension_name = (extension.split('/')[-1]).strip()
            extension_id = "{0}.extension.{1}".format(resource_type, extension_name).strip()
            element_def = {
                "id" : clean_name(extension_id),
                "path" : resource_type+".extension",
                "definition" : row["description"],
                "sliceName" : extension_name,
                "short" : row["label"],
                "min" : extension_min,
                "max": extension_max,
                "type": [{
                    "code": "Extension",
                    "profile": [ get_resource_url('StructureDefinition', extension_name)]
                }],
                "mapping": [
                    {
                        "identity": idx.split('.')[0],
                        "map": idx
                    }
                ]
            }
            element_list.append(element_def)
        else:                        
            path = ''
            if pd.notna(row["map_path"]) and "::" in row["map_path"]:
                profile_details = row["map_path"].strip().split('::')
                profile_min =  profile_details[1].strip()
                profile_max =  profile_details[2].strip()
                path = profile_details[0].strip()
            elif pd.notna(row["map_path"]): 
                profile_min = '0'
                profile_max = '*'
                path = row["map_path"].strip()
            logger.info('Processing path: {0}'.format(path))
            
            if not path:
                continue
            
            ## mapping the element type written in the xls to a corresponding 
            # fhir data type. Special cases with select one have to be 
            # mapped to CodeableConcept and create a binding and valueset in the 
            # element 
            add_binding = False
            add_reference = False
            element_type = row['type']
            id = path
            path = path.split(':')[0]
            if element_type.startswith('select_one'):
                element_valueset_name = element_type.split(' ',1)[-1].strip()
                filtered_valueset = df_valueset.loc[(df_valueset['valueSet']==element_valueset_name) & (df_valueset['code']=='{{url}}')]
                if(not (filtered_valueset).empty):
                    display = filtered_valueset['display'].item()
                    name_of_resource = re.findall('(?:\/[^\/]+)*\/([^\?]+).*',display)[0]
                ## Check if the name after slelect_one starts with a capital or not.
                ## if it has candidateExpression as display we consider it a reference to a profile
                ##Regex to get the name of the resource :(?:\/[^\/]+)*\/([^\?]+).*
                question_display = get_display(row)
                if 'candidateexpression' in question_display :
                    add_reference = True
                    element_type = 'Reference'
                else:
                    element_type = 'CodeableConcept'
                    add_binding = True
            element_def = {
                "id" : clean_name(id), 
                "path" : path.strip(),
                "short" : row["label"],
                "definition" : row["description"],
                "min" : profile_min,
                "max": profile_max,
                "mapping": [
                    {
                        "identity": idx.split('.')[0],
                        "map": idx
                    }
                ]
            }
            if ':' in id:
                element_def['sliceName'] = id.split(':')[1].strip()
            logger.info("id is : ", path +'\n')
            element_def_type = ElementDefinitionType.construct()
            element_def_type.code = get_question_fhir_data_type(element_type)
            if add_reference : 
                element_def_type.targetProfile = [get_fhir_cfg().canonicalBase+\
                    'StructureDefinition/'+row['definition']+'-'+name_of_resource]
            if (add_binding):
                element_def['binding'] = {
                    "extension": [{
                        "url" : "http://hl7.org/fhir/StructureDefinition/elementdefinition-bindingName", 
                        "valueString" : element_valueset_name
                    }],
                    "strength":"extensible",
                    "valueSet" : get_resource_url('ValueSet',element_valueset_name) 
                }
            element_def['type'] = [element_def_type]
            element_list.append(element_def)
    ## At this point, the list of elements should be complete. 
    ## check if there is a slicing in the path of an element 
    ## If there is slicing needed, we need to add the parent with a slicing object 
    ## THis slicing object will have a descriminator with a type and value 
    ## https://simplifier.net/guide/ProfilingAcademy/Slicing for value options
    ## TODO allow for slicing rules? Right now defaults to closed 
    ## TODO Support other types, right now defaulting to type
    ## TODO Support other path, right now defaulting to resolve()
    i = 0 
    while (i < len(element_list)):
        logger.info('indexing through the list, right now at %s', str(i))
        current_element = element_list[i]
        
        if 'sliceName' in current_element.keys():
            parent_min = str(current_element['min'])
            parent_max = str(current_element['max'])
            parent_id = current_element['id'].rsplit('.',1)[0]
            siblings_list = []
            siblings, last_neighbour = check_slice_siblings(siblings_list, element_list, i+1)
            ## checking for the smallest minimum and largest maximum for the parent slicing
            for sibling in siblings:
                if sibling['min'] == '*'  or parent_min=='*':
                    parent_min = '*'
                elif int(sibling['min'])<int(parent_min):
                    parent_min= sibling['min']
                elif sibling['max'] == '*'  or parent_max=='*':
                    parent_max = '*'
                elif int(sibling['max'])> int(parent_max):
                    parent_max = sibling['max']
            parent_element_def = {
                    "id" : clean_name(parent_id),
                    "path" : parent_id,
                    "slicing" : {
                        "discriminator" : [{
                            "type" : "type",
                            "path" : "resolve()"
                        }],
                        "rules" : "closed"
                    }, 
                    "min": parent_min,
                    "max": parent_max
            }
            element_list.append(parent_element_def)
            i+=1
        else: 
            i+=1
    differential = StructureDefinitionDifferential.construct()
    element_list = remove_duplicates(element_list, 'id')
    element_list = [ElementDefinition.parse_obj(el) for el in element_list]
    differential.element = element_list
    profile.differential = differential
    return profile

def check_slice_siblings(siblings_list, element_list, i):
    if i == len(element_list):
        return siblings_list, i
    current_element = element_list[i]
    if not 'sliceName' in current_element.keys():
        return siblings_list, i
    elif 'sliceName' in current_element.keys(): 
        siblings_list.append(current_element)
        return check_slice_siblings(siblings_list, element_list, i+1)
    elif i == len(element_list):
        return siblings_list, i

def remove_duplicates(elements, unique_attribute):
  return list({item[unique_attribute]:item for item in elements}.values())