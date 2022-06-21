""""
tutoral here https://www.hl7.org/fhir/mapping-tutorial.html
Convert XLSsdc quesitonnair to structureMap

"""



import json

import numpy
import pandas as pd
from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from fhir.resources.fhirtypes import Canonical, Code
from pyfhirsdc.serializers.json import read_resource
from fhir.resources.structuremap import StructureMap,\
     StructureMapStructure, StructureMapGroup, StructureMapGroupInput,\
    StructureMapGroupRule, StructureMapGroupRuleSource
from pyfhirsdc.serializers.mappingLanguage import write_mapping_file
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource
from pyfhirsdc.converters.utils import clean_name, get_custom_codesystem_url,  get_resource_url


def get_question_profiles(df_questions):
    profiles = df_questions['map_profile'].dropna().unique()
    return profiles

# generate a single structureMap
def get_structure_map_bundle(questionnaire_name, df_questions):
    structure_maps = []
    profiles = get_question_profiles(df_questions)
    sm_name = get_structure_map_name(profiles, questionnaire_name)
    filepath = get_resource_path(
        "StructureMap", 
        sm_name
    )
    structure_map = init_structure_map(filepath, profiles, questionnaire_name)
    if structure_map is not None:
        map_filepath = get_resource_path("StructureMap", sm_name, "map")
        structure_map.group = get_structure_map_groups(structure_map.group, profiles, questionnaire_name, df_questions)
        if structure_map.group and len(structure_map.group)>0 and structure_map.group[0].name != 'fake':
            structure_map = write_mapping_file(map_filepath, structure_map)
            structure_maps.append(structure_map)
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
        else:
            print("No mapping found for the questionnaire {0}".format(questionnaire_name))

    return structure_maps

def clean_group_name(name):
    return clean_name(name).replace('-','').replace('.','')

def get_structure_maps(questionnaire_name, df_questions):
    structure_maps = []
    profiles = get_question_profiles(df_questions)
    for profile in profiles:
        sm_name = get_structure_map_name([profile], questionnaire_name)
        filepath = get_resource_path(
            "StructureMap", 
            sm_name
            )
        structure_map = init_structure_map(filepath, [profile], questionnaire_name)
        if structure_map is not None:
            map_filepath = get_resource_path("StructureMap", sm_name, "map")
            structure_map.group = get_structure_map_groups(structure_map.group, [profile], questionnaire_name, df_questions)
            #Write the structure map only if the is content
            if structure_map.group and len(structure_map.group)>0 and structure_map.group[0].name != 'fake':
                structure_map = write_mapping_file(map_filepath, structure_map)
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

def init_structure_map(filepath, profiles, questionnaire_name):
    strucutred_map_json = None# read_resource(filepath, "StructureMap")
    default = get_defaut_fhir('StructureMap')
    if strucutred_map_json is not None :
        structure_map = StructureMap.parse_raw( json.dumps(strucutred_map_json))  
    elif default is not None:
        # create file from default
        structure_map = StructureMap.parse_raw( json.dumps(default))
        structure_map.id=get_structure_map_name(profiles, questionnaire_name)
        structure_map.name= structure_map.id
        structure_map.url=get_resource_url("StructureMap", structure_map.id)
        structure_map.structure = get_structure_map_structure(profiles, questionnaire_name)
        
    return structure_map

# 1 structure map per profile and questionnaire
def get_structure_map_name(profiles, questionnaire_name):
    if len(profiles)==1:
        return clean_name(profiles[0]) + "-" + clean_name(questionnaire_name)
    else:
        return clean_name(questionnaire_name)



def get_structure_map_structure(profiles, questionnaire_id):
    structures = []
    # generate source strucutre
    structures.append(StructureMapStructure(
        url = Canonical(  get_resource_url("Questionnaire", questionnaire_id)),
        mode = Code( 'source'),
        alias = clean_group_name(questionnaire_id)

    ))
    for profile in profiles:
        # generate target structure
        structures.append(StructureMapStructure(
            url = Canonical( get_resource_url("StructureDefinition", profile)),
            mode = Code( 'target'),
            alias = clean_group_name(profile)
        ))
    return structures

def get_structure_map_groups(groups, profiles, questionnaire_name, df_questions):
    out_groups = []
    for profile in profiles:
        group_tmp = get_structure_map_generated_group(profile, questionnaire_name, df_questions)
        # clean fake/merge
        if len(groups) == 1 and groups[0].name == 'fake':
             out_groups.append(group_tmp)
        else:
            replaced = False
            for group in groups:           
                if group.name == group_tmp.name:
                    #TODO manage group merge ? 
                    group = group_tmp
                    replaced = True
                    out_groups.append(group)
                    break  
                else:
                    out_groups.append(group)
            if replaced is False:
                out_groups.append(group_tmp)
    return out_groups

def get_structure_map_generated_group(profile, questionnaire_name, df_questions):

    group = StructureMapGroup(
        name = clean_group_name(profile),
        typeMode = Code('types'),
        input = [StructureMapGroupInput(
            mode = Code( 'source'),
            name = "qr",
            type = clean_group_name(questionnaire_name)
        ),
        StructureMapGroupInput(
            mode = Code( 'target'),
            name = "tgt",
            type = clean_group_name(profile)
        )],
        rule = get_structure_map_rules(profile, df_questions)
    )
    return group

def get_structure_map_rules(profile, df_questions):
    rules = []
    questions = df_questions[df_questions['map_profile'] == profile ].to_dict('index')
    for question_name, question in questions.items():
        rule = get_structure_map_rule(question_name,  question)
        if rule is not None:
            rules.append(rule)
    return rules

def get_structure_map_rule(question_name, question):
    #TODO manage transform evaluate/create
    # item that have childer item are created then the children rule will create the children Items
    # example rule 13 and 14 http://build.fhir.org/ig/HL7/sdc/StructureMap-SDOHCC-StructureMapHungerVitalSign.json.html
    #profileType, element, valiable = explode_map_resource(question['map_resource'])
    rule = None
    #print("Mapping ``{0}`` added".format(fhirmapping))
    if  'map_resource' in question\
        and pd.notna(question['map_resource'])\
        and question['map_resource'] is not None:
        is_complex = str(question['map_resource']).find(',') != -1\
            or str(question['map_resource']).find('{') != -1\
            or str(question['map_resource'][:-1]).find(';') != -1
        if question['map_resource'][-1:] != ";":
            question['map_resource'] = question['map_resource'] + " '"+ question_name + "-1';"
        # if variable on root, element is the resource itself
        fhirmapping = "item.answer first as a where item.linkId = '"\
            + question_name + "'  then { "\
            + question['map_resource'] + " }"
        fhirmapping = fhirmapping.replace('{{cs_url}}',  get_custom_codesystem_url())
        fhirmapping = fhirmapping.replace('{{canonical_base}}',  get_fhir_cfg().canonicalBase)
        rule = StructureMapGroupRule(
            name = question_name,
            source = [StructureMapGroupRuleSource(
                context = 'item',
            )],
            documentation = fhirmapping,  
            )
    return rule