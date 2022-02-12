""""
tutoral here https://www.hl7.org/fhir/mapping-tutorial.html
Convert XLSsdc quesitonnair to structureMap

"""



import json
from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from fhir.resources.fhirtypes import Canonical, Code
from pyfhirsdc.serializers.json import read_resource
from fhir.resources.structuremap import \
    StructureMap, StructureMapStructure, StructureMapGroup, StructureMapGroupInput,\
    StructureMapGroupRule, StructureMapGroupRuleSource, StructureMapGroupRuleTarget,\
    StructureMapGroupRuleTargetParameter

from pyfhirsdc.utils import clean_name, get_resource_path, get_resource_url, write_resource


def get_question_profiles(df_questions):
    profiles = df_questions['map_profile'].dropna().unique()
    return profiles

def get_structure_maps(questionnaire_name, df_questions):
    structure_maps = []
    profiles = get_question_profiles(df_questions)
    for profile in profiles:
        sm_name = profile.replace(" ","-").lower() + "-" + questionnaire_name
        filepath = get_resource_path(
            "StructureMap", 
            sm_name
            )
        structure_map = init_structure_map(filepath, profile, questionnaire_name)
        if structure_map is not None:
            structure_maps.append(structure_map)
            structure_map.group = get_structure_map_groups(structure_map.group, profile, questionnaire_name, df_questions)
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
    return structure_maps

def add_structure_maps_url(resource, structure_maps):
    for structure_map in structure_maps:
        resource.extension = get_structure_map_extension(
            resource.extension, 
            structure_map.url
            )
    return resource

def init_structure_map(filepath, profile, questionnaire_name):
    strucutred_map_json = read_resource(filepath, "StructureMap")
    default =get_defaut_fhir('StructureMap')
    if strucutred_map_json is not None :
        structure_map = StructureMap.parse_raw( json.dumps(strucutred_map_json))  
    elif default is not None:
        # create file from default
        structure_map = StructureMap.parse_raw( json.dumps(default))
        structure_map.id=get_structure_map_name(profile, questionnaire_name)
        structure_map.name= structure_map.id
        structure_map.url=get_resource_url("StructureMap", structure_map.id)
        structure_map.structure = get_structure_map_structure(profile, questionnaire_name)
        
    return structure_map


def get_structure_map_name(profile, questionnaire_name):
    return clean_name(profile) + "-" + questionnaire_name



def get_structure_map_structure(profile, questionnaire_name):
    structures = []
    # generate source strucutre
    structures.append(StructureMapStructure(
        url = Canonical(  get_resource_url("Questionnaire", questionnaire_name)),
        mode = Code( 'source'),
        alias = clean_name(questionnaire_name)

    ))
    # generate target structure
    structures.append(StructureMapStructure(
        url = Canonical( get_resource_url("Profile", profile)),
        mode = Code( 'target'),
        alias = clean_name(profile)
    ))
    return structures

def get_structure_map_groups(groups, profile, questionnaire_name, df_questions):
    groups = []
    group_tmp = get_structure_map_generated_group(profile, questionnaire_name, df_questions)
    # clean fake/merge
    replaced = False
    for group in groups:
        if group.name != 'fake':
            if group.name == group_tmp.name:
                group = merge_structure_map_groups(group, group_tmp)
                replaced = True
            groups.append(group)
    if replaced is False:
        groups.append(group_tmp)
    return groups

def get_structure_map_generated_group(profile, questionnaire_name, df_questions):

    group = StructureMapGroup(
        name = "main",
        typeMode = Code('types'),
        input = [StructureMapGroupInput(
            mode = Code( 'source'),
            name = clean_name(questionnaire_name)
        ),
        StructureMapGroupInput(
            mode = Code( 'target'),
            name = clean_name(profile)
        )],
        rule = get_structure_map_rules(profile, questionnaire_name, df_questions)

    )
    return group

def get_structure_map_rules(profile, questionnaire_name, df_questions):
    rules = []
    questions = df_questions[df_questions['map_profile'] == profile ].to_dict('index')
    for question_name, question in questions.items():
        rule = get_structure_map_rule(profile, questionnaire_name, question_name,  question)
        if rule is not None:
            rules.append(rule)

    return rules

def get_structure_map_rule(profile, questionnaire_name,question_name, question):
    #TODO manage transform evaluate/create
    # item that have childer item are created then the children rule will create the children Items
    # example rule 13 and 14 http://build.fhir.org/ig/HL7/sdc/StructureMap-SDOHCC-StructureMapHungerVitalSign.json.html
    profileType, element, valiable = explode_map_resource(question['map_resource'])
      
    if  valiable is not None:
        # if variable on root, element is the resource itself
        if element is None or element == '':
            element = 'resource'
        rule = StructureMapGroupRule(
            name = question_name,
            source = [StructureMapGroupRuleSource(
                context = 'item',
                variable = question_name
            )],
            target = [StructureMapGroupRuleTarget(
                context = clean_name(profile),
                contextType = 'variable',
                element = element,
                transform = Code('copy'),
                parameter= [StructureMapGroupRuleTargetParameter(
                    valueString = valiable)]
            )]
    )

    return rule


def get_structure_map_rule_parameter(question, valiable):

    
    if question['map_resource_type'] == 'decimal':
        return StructureMapGroupRuleTargetParameter(
             valueDecimal = valiable
            )
    elif question['map_resource_type'] == 'integer':
        return StructureMapGroupRuleTargetParameter(
             valueInteger = valiable
            )
    elif question['map_resource_type'] == 'CodeableConcept' or\
         'Reference' in question['map_resource_type'] :
        # if 'select_' in question['type']:
        return StructureMapGroupRuleTargetParameter(
             valueId = valiable
            )
    elif question['map_resource_type'] == 'boolean':
        return StructureMapGroupRuleTargetParameter(
             valueBoolean = valiable
            )
    elif question['map_resource_type'] == 'string': 
        return StructureMapGroupRuleTargetParameter(
            valueString = valiable
            )
    else:  
        return StructureMapGroupRuleTargetParameter(
            valueString = valiable
            )

def explode_map_resource(map_resource):
    resource_path = map_resource.split('.')
    variable = resource_path[-1]
    profile = resource_path[0]
    element = '.'.join(resource_path[1:-1])
    return profile, element, variable

def merge_structure_map_groups(group_old, group_new):
    # TODO: manage the merge
    return group_new