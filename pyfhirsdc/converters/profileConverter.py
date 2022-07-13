from importlib.resources import path
from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.structuredefinition import StructureDefinition
from fhir.resources.structuredefinition import StructureDefinitionDifferential
from fhir.resources.fhirtypes import Id
from fhir.resources.fhirtypes import Uri
from fhir.resources.fhirtypes import Code
from fhir.resources.extension import Extension
import re
from fhir.resources.elementdefinition import ElementDefinitionType
from fhir.resources.fhirtypes import StructureDefinitionContextType
from fhir.resources.elementdefinition import ElementDefinition
from pyfhirsdc.converters.questionnaireItemConverter import get_question_fhir_data_type
import pandas as pd
import validators

from pyfhirsdc.converters.utils import clean_name, get_resource_name, get_resource_url
# allow slice in ID and extention MedicationRequest.medication[x].coding or MedicationRequest.medication[x].extension:notDoneValueSet Observation.modifierExtension:notDone.value[x]

Id.configure_constraints(regex=re.compile(r"^[A-Za-z0-9\-\.]+(\[x\](\.[a-zA-Z]+)?)?(:[A-Za-z0-9\-.]+(\[x\](\.[a-zA-Z]+)?)?)?$"))      

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
        print(extension_name)
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
                path = "Extension.value[x]",
                short = extension_name,
                definition = element['description'],
                min = min_cardinality,
                max = max_cardinality
            )
        ]
        element_type = element['type']
        add_reference = False
        if element_type.startswith('select_one'):
            element_valueset_name = element_type.split(' ',1)[-1]
            ## Check if the name after slelect_one starts with a capital or not.
            ## if it starts with a capital it is a reference to a profile
            print("name of the value set: ",element_type)
            if element_valueset_name[0].isupper():
                add_reference = True
                element_type = 'Reference'
            else:
                element_type = 'CodeableConcept'
                add_binding = True
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


def convert_df_to_profiles(df_questions, df_profile, df_valueset):
    profiles = []
    names = []
    q_idx = []
    #Grouping rows based on the profiles, so that we can go through the different groups and create
    # the corresponding profiles with the right attributes
    grouped_profiles = df_questions.groupby('map_profile')
    #for key, item in grouped_profiles:
    #    print("Profile: ", key)
    #    print(grouped_profiles.get_group(key), "\n\n")

    for idx, row in df_profile.iterrows():
        profile, name = init_profile_def(row)
        if name in grouped_profiles.groups:
            names.append(name)
            profile = extend_profile(name,profile, grouped_profiles.get_group(name), df_valueset)
            profiles.append(profile)
    return profiles,names


def init_profile_def(element):
    path = element['baseProfile']
    structure_def_name_list = element['title'].split(' ',1)
    structure_def_name = ' '.join(structure_def_name_list)
    structure_def_scaffold = {
        "resourceType" : "StructureDefinition",
        "kind" : Code('complex-type'),
        "title" : structure_def_name,
        "abstract" : False,
        "name" : structure_def_name,
        "status" : Code('draft'), 
        "type" : structure_def_name_list[-1],
        "url" : get_resource_url('StructureDefinition', Id(structure_def_name.replace(' ', '-')))
    }
    if pd.notna(path):
        structure_def_scaffold['baseDefinition'] = Uri(path)
        structure_def_scaffold["derivation"] = "constraint"
    structure_def = StructureDefinition.parse_obj(structure_def_scaffold)
    structure_def.id = clean_name(structure_def_name)
    structure_def.experimental = False
    structure_def.fhirVersion = get_fhir_cfg().version
    structure_def.description = element['description']
    return structure_def, structure_def_name

def extend_profile(name, profile, grouped_profile, df_valueset):
    resource_type = name.split(' ', 1 )[-1].strip()
    element_list = []
    element_list.append({
        "id": clean_name(resource_type),
        "path": resource_type
    })
    print('Processing Profile: {0}'.format(name))
    for idx, row in grouped_profile.iterrows():
        # if there is a map_extension then we have to link it to the extension and 
        # add a slice name
        extension = row["map_extension"]
        is_profile = pd.notna(row["map_profile"])

        if not pd.notna(row["map_profile"]) and not pd.notna(row["map_path"]):
            continue
        if pd.notna(extension) and is_profile:
            if "::" in extension:
                extension_details =extension.strip().split('::')
                extension_name= extension_details[0].split('/')[-1]
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
            print('Processing path: {0}'.format(path))
            
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
                if row['display'] =='candidateExpression':
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
            print("id is : ", path +'\n')
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
        print('indexing through the list, right now at ', i)
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