from importlib.resources import path
import resource
from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.structuredefinition import StructureDefinition
from fhir.resources.structuredefinition import StructureDefinitionDifferential
from fhir.resources.fhirtypes import Id
from fhir.resources.fhirtypes import Uri
from fhir.resources.fhirtypes import Code
from fhir.resources.extension import Extension
from fhir.resources.fhirtypes import StructureDefinitionContextType
from fhir.resources.elementdefinition import ElementDefinition
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
    extension_path = map_extension[0].replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)
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
        "url" : Uri(extension_path)
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
            "max" : max_cardinality, 
            "type" : [
                {
                    "code" : element["type"]
                }],
        })
    ]
    differential = StructureDefinitionDifferential.construct()
    differential.element = extension_element
    structure_def.differential = differential
    return structure_def, structure_def_slice_name


def convert_df_to_profiles(df_questions, df_profile):
    profiles = []
    names = []
    grouped_profiles = df_questions.groupby('map_profile')
    
    #for key, item in grouped_profiles:
    #    print("Profile: ", key)
    #    print(grouped_profiles.get_group(key), "\n\n")

    for idx, row in df_profile.iterrows():
        profile, name = init_profile_def(row)
        names.append(name)
        if name in grouped_profiles.groups:
            profile = extend_profile(name,profile, grouped_profiles.get_group(name)) 
        profiles.append(profile)
    return profiles, names


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
        "url" : Uri(canonical+"/StructureDefinition/"+structure_def_name)
    }
    structure_def = StructureDefinition.parse_obj(structure_def_scaffold)
    structure_def.id = Id(structure_def_name.replace(' ', '-'))
    structure_def.experimental = False
    structure_def.fhirVersion = get_fhir_cfg().version
    structure_def.description = element['description']
    return structure_def, structure_def_name

def extend_profile(name, profile, grouped_profile, canonical):
    resource_type = name.split(' ', 1 )[-1]
    element_list = []
    element_list.append({
        "id": name,
        "path": name
    })
    for idx, row in grouped_profile.iterrows():
        # if there is a map_extension then we have to link it to the extension and 
        # add a slice name
        extension = row["map_extension"] 
        if extension:
            extension_details =extension.split('::') 
            extension_name= extension_details[0].split('/')[-1]
            extension_min =  extension_details[1]
            extension_max =  extension_details[2]
            element_def = ElementDefinition.parse_obj(
            {
                "id" : resource_type+".extension:"+extension_name,
                "path" : resource_type+".extension",
                "sliceName" : extension_name,
                "short" : row["label"],
                "min" : extension_min,
                "max": extension_max,
                "type": [{
                    "code": "Extension",
                    "profile": [get_fhir_cfg().canonicalBase+'StructureDefinition/'+extension_name]
                }],
                "mapping": [
                    {
                        "identity": row["scope"],
                        "map": idx
                    }
                ]
            })
            element_list.append(element_def)
        else:
            element_def = ElementDefinition.parse_obj(
            {
                "id" : resource_type+".extension:"+extension_name,
                "path" : resource_type+".extension",
                "sliceName" : extension_name,
                "short" : row["label"],
                "min" : extension_min,
                "max": extension_max,
                "type": [{
                    "code": "Extension",
                    "profile": [get_fhir_cfg().canonicalBase+'StructureDefinition/'+extension_name]
                }],
                "mapping": [
                    {
                        "identity": row["scope"],
                        "map": idx
                    }
                ]
            })
            element_list.append(element_def)
    differential = StructureDefinitionDifferential.construct()
    differential.element = element_list
    profile.differential = differential
    return profile