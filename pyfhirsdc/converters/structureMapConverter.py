""""
tutoral here https://www.hl7.org/fhir/mapping-tutorial.html
Convert XLSsdc quesitonnair to structureMap

"""



import json
from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from pyfhirsdc.serializers.json import read_resource
from fhir.resources.structuremap import StructureMap

from pyfhirsdc.utils import get_resource_path, write_resource


def get_question_profiles(df_questions):
    profiles = df_questions['map_custom_profile_id'].dropna().unique()

    return profiles

def get_structure_maps(name, df_questions):
    structure_maps = []
    profiles = get_question_profiles(df_questions)
    for profile in profiles:
        sm_name = profile.replace(" ","-").lower() + "-" + name
        filepath = get_resource_path(
            "StructureMap", 
            sm_name
            )
        structure_map = init_structure_map(filepath, sm_name)
        if structure_map is not None:
            structure_maps.append(structure_map)
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
    return structure_maps

def add_structure_maps_url(resource, structure_maps):
    for structure_map in structure_maps:
        resource.extension = get_structure_map_extension(
            resource.extension, 
            structure_map.url
            )
    return resource

def init_structure_map(filepath, id):
    strucutred_map_json = read_resource(filepath, "StructureMap")
    default =get_defaut_fhir('StructureMap')
    if strucutred_map_json is not None :
        structure_map = StructureMap.parse_raw( json.dumps(strucutred_map_json))  
    elif default is not None:
        # create file from default
        structure_map = StructureMap.parse_raw( json.dumps(default))
        structure_map.id=id
        structure_map.name=id
        structure_map.url=get_fhir_cfg().canonicalBase\
            + "/structureMap/" \
            + id
    return structure_map