"""
Serializer to write the map file from a StructureMAp where 
the mapping language is define in the rule description

"""


import numpy
import json
from pyfhirsdc.config import get_fhir_cfg
from pyfhirsdc.serializers.utils import write_resource
import requests
from fhir.resources.structuremap import StructureMap

def write_mapping_file(filepath, structure_map, update_map = True):

    buffer = get_mapping_file_header(structure_map)\
            + get_mapping_file_groups(structure_map)
    write_resource(
        filepath,
         buffer
        , 'map'
        )
    if update_map:
        url_map= get_fhir_cfg().canonicalBase + '/StructureMap'
        headers_map = {'Content-type': 'text/fhir-mapping', 'Accept': 'application/fhir+json;fhirVersion=4.0'}
        response = requests.post(url_map, data = buffer, headers = headers_map) 
        if response.status_code == 200 or response.status_code == 201:
            obj = json.loads(response.text)
            obj['status'] = 'draft'
            structure_map = structure_map.parse_raw( json.dumps(obj))
        else:
            print(str(response.status_code) +":"+ structure_map.id)
            print(response.text)

    return structure_map



def get_mapping_file_header(structure_map):

    # structure map def
    header = "map '" + structure_map.url + "' = '" + structure_map.name + "'\n\n"
    # get the source / Source
    for in_output in structure_map.structure:
        header = header + "uses '" + in_output.url + "' alias '"\
             + str(in_output.alias).strip("'") + "' as " + in_output.mode + "\n"
    
    return header

def get_mapping_file_groups(structure_map):
    group_buffer = ''
    for group in structure_map.group:
        group_buffer = group_buffer + get_mapping_file_group(group)
    return group_buffer


def get_mapping_file_group(group):
    # execute (in case of bundle)
    source = ''
    target = ''
    # define 
    group_buffer =  'group  ' + group.name + "(\n"
    i = 1
    for in_output in group.input:
        if in_output.mode is not None\
            and in_output.name is not None\
            and in_output.type is not None :
            group_buffer = group_buffer + "\t" + in_output.mode + " "\
                + in_output.name + " : '" + in_output.type + "'"
            group_buffer = group_buffer + ",\n" if i < len(group.input)\
                else group_buffer + "\n"
            if in_output.mode == 'source':
                source = in_output.type
            elif in_output.mode == 'target':
                target = in_output.type
        i+=1
    
    group_buffer =  group_buffer + ") {\n"
    # write Items subsection
    if group.rule is not None and group.rule != [] :
        group_buffer = group_buffer + "\t" + "qr.item as item then {\n"
        # write item mapping
        for rule in group.rule:
            if rule.documentation is not None\
            and rule.name is not None:
                group_buffer = group_buffer + "\t\t" +  str(rule.documentation) + " '" + rule.name + "';\n"
        # close Items subsection 
        group_buffer = group_buffer + "\t} 'items"+ source + "-" + target +"';\n"  
    # close group
    group_buffer = group_buffer + "} \n\n"
        
    
    return group_buffer
