from importlib.resources import path
from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.structuredefinition import StructureDefinition
from fhir.resources.structuredefinition import StructureDefinitionDifferential
from fhir.resources.fhirtypes import Id
from fhir.resources.fhirtypes import Uri
from fhir.resources.fhirtypes import Code
from fhir.resources.extension import Extension
from fhir.resources.elementdefinition import ElementDefinitionType
from fhir.resources.fhirtypes import StructureDefinitionContextType
from fhir.resources.elementdefinition import ElementDefinition
from pyfhirsdc.converters.questionnaireItemConverter import get_question_fhir_data_type
import pandas as pd 

def convert_df_to_extension_profiles(df):
    rows_with_extensions = df[pd.notna(df['map_extension'])]
    extensions = []
    names = []
    for idx, row in rows_with_extensions.iterrows():
        std_def, name = init_extension_def(row)
        names.append(name)
        extensions.append(std_def)
    return extensions, names

def init_extension_def(element):
    map_extension = element['map_extension'].split('::')
    ## Check for the map resource of the extension and grab the extension URL
    ## Replace the Canonical base URL placeholder with the real url 
    extension_path = (map_extension[0].replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)).strip()
    structure_def_slice_name =extension_path.split('/')[-1].strip()
    structure_def_id = extension_path
    # Pydantics does not allow to add a property to an object without providing all the 
    # mandatory fields. So first this object has to be created 
    structure_def_scaffold = {
        "resourceType" : "StructureDefinition",
        "kind" : Code('complex-type'),
        "abstract" : False,
        "name" : structure_def_slice_name,
        "status" : Code('draft'), 
        "type" : "Extension",
        "url" : Uri(extension_path).strip()
    }
    structure_def = StructureDefinition.parse_obj(structure_def_scaffold)
    structure_def.id = Id(structure_def_slice_name)
    structure_def.experimental = False
    structure_def.fhirVersion = get_fhir_cfg().version
    structure_def.description = element['description']
    if pd.notna(element["map_profile"]):
        structure_def.context = [StructureDefinitionContextType({"type": "element",\
            "expression": element['map_profile'].split(' ',1)[1]})]
    structure_def.type = "Extension"
    structure_def.baseDefinition = "http://hl7.org/fhir/StructureDefinition/Extension"
    structure_def.derivation = "constraint"
    min_cardinality = map_extension[1].strip()
    max_cardinality = map_extension[2].strip()
    extension_element = [ElementDefinition.parse_obj(
        {
            "id":"Extension",
            "path" : "Extension",
            "short" :structure_def_slice_name,
            "definition": element['description'],
            "min" : min_cardinality,
            "max" : max_cardinality
        }),
        ElementDefinition.parse_obj({
            "id" : "Extension.extension",
            "path" : "Extension.extension",
            "min" : min_cardinality,
            "max" : max_cardinality
        }),
        ElementDefinition.parse_obj({
            "id" : "Extension.url",
            "path" : "Extension.url",
            "fixedUri" : Uri(extension_path),
        }), 
        ElementDefinition.parse_obj({
            "id": "Extension.value",
            "path" : "Extension.value[x]",
            "short" : structure_def_slice_name,
            "definition" : element['description'],
            "min" : min_cardinality,
            "max" : max_cardinality
        })
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
        print('Writing target PROFILE')
        element_def_type.targetProfile = [get_fhir_cfg().canonicalBase+\
                'StructureDefinition/'+element['definition']+'-'+element_valueset_name]
    extension_element[-1].type = [element_def_type]
    differential = StructureDefinitionDifferential.construct()
    differential.element = extension_element
    structure_def.differential = differential
    return structure_def, structure_def_slice_name


def convert_df_to_profiles(df_questions, df_profile):
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
            profile = extend_profile(name,profile, grouped_profiles.get_group(name))
            profiles.append(profile)
    return profiles,names


def init_profile_def(element):
    path = element['baseProfile']
    canonical = get_fhir_cfg().canonicalBase
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
        "baseDefinition" : Uri(path),
        "url" : Uri(canonical+"/StructureDefinition/"+structure_def_name.replace(' ', '-')).strip()
    }
    structure_def = StructureDefinition.parse_obj(structure_def_scaffold)
    structure_def.id = Id(structure_def_name.replace(' ', '-'))
    structure_def.experimental = False
    structure_def.fhirVersion = get_fhir_cfg().version
    structure_def.description = element['description']
    return structure_def, structure_def_name

def extend_profile(name, profile, grouped_profile):
    resource_type = name.split(' ', 1 )[-1]
    element_list = []
    element_list.append({
        "id": resource_type,
        "path": resource_type
    })
    print('Processing Profile: {0}'.format(name))
    for idx, row in grouped_profile.iterrows():
        # if there is a map_extension then we have to link it to the extension and 
        # add a slice name
        extension = row["map_extension"] 
        if not pd.notna(row["map_profile"]) and not pd.notna(row["map_path"]):
            continue
        if pd.notna(extension):
            if "::" in extension:
                extension_details =extension.split('::')
                extension_name= extension_details[0].split('/')[-1]
                extension_min =  extension_details[1]
                extension_max =  extension_details[2]
            else: 
                extension_min = '0'
                extension_max = '*'
                extension_name = (extension.split('/')[-1]).strip()
            print('Processing extension: {0}'.format(extension_name))
            extension_id = "{0}.extension.{1}".format(resource_type.strip(), extension_name.strip())
            print('The id of the extension is:',(extension_id) )
            element_def = ElementDefinition.parse_obj(
            {
                "id" : extension_id,
                "path" : resource_type+".extension",
                "definition" : row["description"],
                "sliceName" : extension_name,
                "short" : row["label"],
                "min" : extension_min.strip(),
                "max": extension_max.strip(),
                "type": [{
                    "code": "Extension",
                    "profile": [get_fhir_cfg().canonicalBase+'StructureDefinition/'+extension_name]
                }],
                "mapping": [
                    {
                        "identity": idx.split('.')[0],
                        "map": idx
                    }
                ]
            })
            element_list.append(element_def)
        else:
            path = ''
            if pd.notna(row["map_path"]) and "::" in row["map_path"]:
                profile_details = row["map_path"].split('::')
                profile_min =  profile_details[1]
                profile_max =  profile_details[2]
                path = profile_details[0]
            elif pd.notna(row["map_path"]): 
                profile_min = '0'
                profile_max = '*'
                path = row["map_path"]
            if not path:
                continue
            print('Processing extension: {0}'.format(path))
            ## check if there is a slicing in the path looking for semicolon (:)
            slice_name = path.split('.')[-1]
            if slice_name.startswith(':'):
                slice_name = slice_name.replace(':', '')
            element_type = row['type']
            ## mapping the element type written in the xls to a corresponding 
            # fhir data type. Special cases with select one have to be 
            # mapped to CodeableConcept and create a binding and valueset in the 
            # element 
            add_binding = False
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
                    
            print("add reference? ", add_reference)
            ## create function similar to get_fhir_question_type
            
            print("id is : ", path.strip() +'\n')
            print(row["description"])
            element_def = ElementDefinition.parse_obj(
            {
                "id" : path.strip(), 
                "path" : path,
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
            })
            element_def_type = ElementDefinitionType.construct()
            element_def_type.code = get_question_fhir_data_type(element_type)
            if add_reference : 
                element_def_type.targetProfile = [get_fhir_cfg().canonicalBase+\
                    'StructureDefinition/'+row['definition']+'-'+element_valueset_name]
            
            if (add_binding):
                element_def.binding = {
                    "extension": [{
                        "url" : "http://hl7.org/fhir/StructureDefinition/elementdefinition-bindingName", 
                        "valueString" : element_valueset_name
                    }],
                    "strength":"extensible",
                    "valueSet" : get_fhir_cfg().canonicalBase+"/ValueSet/valueset-"+element_valueset_name
                }
            element_def.type = [element_def_type]
            element_def.sliceName = slice_name 
            element_list.append(element_def)
    differential = StructureDefinitionDifferential.construct()
    differential.element = element_list
    profile.differential = differential
    return profile