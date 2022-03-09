from importlib.resources import path
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
    print(map_extension)
    extension_element = [ElementDefinition.parse_obj(
        {
            "id":"Extension",
            "path" : "Extension",
            "short" :structure_def_slice_name,
            "definition": element['description'],
            "min" : map_extension[1],
            "max" : map_extension[2]
        }),
        ElementDefinition.parse_obj({
            "id" : "Extension.extension",
            "path" : "Extension.extension",
            "min" : map_extension[1],
            "max" : map_extension[2]
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
            "min" : map_extension[1],
            "max" : map_extension[2], 
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


def convert_df_to_profiles():
    return