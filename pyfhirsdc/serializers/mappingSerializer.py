import json
import logging

import requests
from fhir.resources.R4B.structuremap import StructureMap

from pyfhirsdc.serializers.http import check_internet
from pyfhirsdc.serializers.utils import reindent, write_resource

from ..config import add_tail_slash, get_processor_cfg

logger = logging.getLogger("default")

def write_mapping_file(filepath, mapping, update_map = True):

    buffer = write_mapping_file_header(mapping)\
            + write_mapping_file_groups(mapping)
    write_resource(
        filepath,
         buffer
        , 'map'
        )
    structure_map = None
    if update_map and check_internet():
        
        url_map=   add_tail_slash(get_processor_cfg().mapping_translator) + mapping.name
        logger.debug("Sending the mapping file {0}".format(url_map))
        headers_map = {'Content-type': 'text/fhir-mapping', 'Accept': 'application/fhir+json;fhirVersion=4.0'}
        response = requests.put(url_map, data = buffer, headers = headers_map) 
        if response.status_code == 200 or response.status_code == 201:
            obj = json.loads(response.text)
            obj['status'] = 'active'
            obj['id'] = mapping.name
            # to avoid having change at regeneration
            del obj['meta']
            structure_map = StructureMap.parse_raw( json.dumps(obj))
        else:
            logger.debug(str(response.status_code) +":"+ mapping.name)
            logger.warning(response.text)

    return structure_map

def write_mapping_file_header(mapping):
    buffer = "map '{0}' = '{1}'\n".format(mapping.url, mapping.name)
    for source in mapping.sources:
        buffer += "uses '{0}' alias '{1}' as source\n".format(source.url, source.alias)
    for target in mapping.targets:
        buffer += "uses '{0}' alias '{1}' as target\n".format(target.url, target.alias)
    for product in mapping.products:
        buffer += "uses '{0}' alias '{1}' as produced\n".format(product.url, product.alias)    
    return buffer

def write_mapping_file_groups(mapping):
    buffer = ''
    for group in mapping.groups:
        buffer += write_mapping_file_group(group)
    return buffer
        
def write_mapping_file_group(group):
    buffer = 'group {}('.format(group.name)
    for source in group.sources:
        if source.type is None:
            buffer += "source {0},".format(source.name)
        else:   
            buffer += "source {0} : {1},".format(source.name, source.type)
    for target in group.targets:
        if target.type is None:
            buffer += "target {0},".format(target.name)
        else:   
            buffer += "target {0} : {1},".format(target.name, target.type) 
    buffer =  buffer[:-1] + "){\n"
    for rule in group.rules: 
        buffer += reindent(write_mapping_file_rule(rule),4) + "\n"
#    for sub_group in group.groups: 
#        buffer += reindent(write_mapping_file_group(sub_group),4)+ "\n"
    buffer+="}\n\n"
    return buffer
    
def write_mapping_file_rule(rule):
    buffer = rule.expression
    if len(rule.rules)>0:
        buffer += " then {\n"
        for sub_rule in rule.rules:
            buffer += reindent(write_mapping_file_rule(sub_rule),4)+ "\n"
        buffer += "\n}"
    buffer += " '{1}';".format(rule.expression, rule.name)
    return buffer  