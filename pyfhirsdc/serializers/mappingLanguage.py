"""
Serializer to write the map file from a StructureMAp where 
the mapping language is define in the rule description

"""


import numpy
import json
from pyfhirsdc.converters.utils import get_resource_url
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
        
        url_map= get_resource_url('StructureMap', structure_map.id)
        print("Sending the mapping file {0}".format(url_map))
        headers_map = {'Content-type': 'text/fhir-mapping', 'Accept': 'application/fhir+json;fhirVersion=4.0'}
        response = requests.put(url_map, data = buffer, headers = headers_map) 
        if response.status_code == 200 or response.status_code == 201:
            obj = json.loads(response.text)
            obj['status'] = structure_map.status
            obj['id'] = structure_map.id
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
        header += "// {3}\nuses '{0}' alias '{1}' as {2}\n".format(
            in_output.url,
            str(in_output.alias).strip("'"),
            in_output.mode,
            in_output.documentation if in_output.documentation is not None else ''
            )
    return header

def get_mapping_file_groups(structure_map):
    group_buffer = ''
    # du bundle if ressource found
    if len(structure_map.group):
        group_buffer += get_group_bundle_header()
        for group in structure_map.group:
            cur_group = get_group_bundle(group)
            if cur_group is not None:
                group_buffer += cur_group
        group_buffer += "}\n\n"
    for group in structure_map.group:
        if len(group.rule) > 0:
            group_buffer += get_mapping_file_group(group)
        elif group.documentation is not None:
            group_buffer += group.documentation + "\n\n"
    return group_buffer

def get_group_bundle_header():
    return "group bundleMapping(source src : questionnaireResponse, target bundle : Bundle) {\n\
            src -> bundle.id = uuid() 'id';\n\
            src -> bundle.type = 'transaction' 'type';\n"


def get_group_bundle(group):
    profile = None
    for in_output in group.input:
        if in_output.mode == 'target':
                profile = in_output.type
    if profile is not None:
        rule = "src -> bundle.entry as entry, entry.resource = create('{0}') as tgt then {1}(src, tgt) '{1}rule';\n".format(
            profile, 
            group.name + "group"
        )
        return rule
    else:
        print("group {} without target".format(group.name))


def get_mapping_file_group(group):
    # execute (in case of bundle)
    source = ''
    target = ''
    # define 
    group_buffer =  'group  ' + group.name + "group" + "(\n"
    i = 1
    for in_output in group.input:
        if in_output.mode is not None\
            and in_output.name is not None\
            and in_output.type is not None :
            group_buffer = group_buffer + "\t" + in_output.mode + " "\
                + in_output.name + " : " + in_output.type 
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
        
        # write item mapping
        for rule in group.rule:
            if rule.documentation is not None\
            and rule.name is not None:
                group_buffer = group_buffer + "\t\t" +  str(rule.documentation) +  "\n"
 
    # close group
    group_buffer = group_buffer + "} \n\n"
        
    
    return group_buffer


def get_observation_yes_no_group(mode, canonicalBase = 'http://build.fhir.org',observation='Observation'):
    
    return "group TransformObservationYesNo(source src: questionnaireResponse, source answerItem, target observation: Observation, target entry)\n\
    {\n\
    src -> observation.basedOn = src.basedOn; 'careplan'\n\
    answerItem.answer as answer -> observation.value = create('CodeableConcept') as newCC then {\n\
        answer.valueCoding as coding -> newCC.coding = coding as newCoding;\n\
    };\n\
    answerItem.answer as answer then {\n\
        answer.valueCoding as Coding where Coding.code == 'yes' -> observation.status = 'final' 'found';\n\
        answer.valueCoding as Coding where Coding.code == 'no' -> observation.status = 'cancelled' 'not-found';\n\
    } 'status';\n\
  };"#.format(canonicalBase,observation)
    #//src -> observation.meta = create('Meta') as newMeta then {\n\
    #//src -> newMeta.profile = '{0}/StructureDefinition/{1}';\n\



