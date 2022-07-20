""""
tutoral here https://www.hl7.org/fhir/mapping-tutorial.html
Convert XLSsdc quesitonnair to structureMap

"""



import json

import pandas as pd
from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from fhir.resources.fhirtypes import Canonical, Code
from fhir.resources.structuremap import StructureMap,\
     StructureMapStructure, StructureMapGroup, StructureMapGroupInput,\
    StructureMapGroupRule, StructureMapGroupRuleSource
from pyfhirsdc.serializers.utils import  get_resource_path, write_resource
from pyfhirsdc.converters.utils import clean_name, get_custom_codesystem_url,  get_resource_url
import requests
from fhir.resources.structuremap import StructureMap


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
    return clean_name(name).replace('-','').replace('.','').replace('/','')

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

FHIR_BASE_PROFILES = [
    "Patient",
    "RelatedPerson",
    "Encounter",
    "Condition",
    "Observation",
    "QuestionnaireResponse",
    "CommunicationRequest"
]


def get_base_profile(profile):
    for base_profile in FHIR_BASE_PROFILES:
        if base_profile.lower() in profile.lower():
            return base_profile



def get_structure_map_structure(profiles, questionnaire_id):
    structures = []
    # generate source strucutre
    structures.append(StructureMapStructure(
        url = Canonical('http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaireresponse'),
        mode = Code( 'source'),
        alias = 'questionnaireResponse',
        documentation = clean_group_name(questionnaire_id) + ":" + get_resource_url("Questionnaire", questionnaire_id)

    ))
    if len(profiles)>0:
        structures.append(StructureMapStructure(
            url = Canonical('http://hl7.org/fhir/StructureDefinition/Bundle'),
            mode = Code( 'target'),
            alias = 'bundle',
            documentation = "Bundle are require where there is multiple ressource to be mapped"
        ))

    for profile in profiles:
        # generate target structure
        base_name = get_base_profile(profile)
        base_url = "http://hl7.org/fhir/StructureDefinition/"+base_name
        structures.append(StructureMapStructure(
            url = Canonical(base_url ),
            mode = Code( 'target'),
            alias = base_name,
            documentation = "target that will be inserted in the bundle"
        ))        
        structures.append(StructureMapStructure(
            url = Canonical( get_resource_url("StructureDefinition", profile)),
            mode = Code( 'produced'),
            alias = clean_group_name(profile),
            documentation = "profile that will be inserted in the bundle"
        ))
    return structures

# generate tth StructureMap content
def get_structure_map_groups(groups, profiles, questionnaire_name, df_questions):
    out_groups = []
    for profile in profiles:
        base_profile = get_base_profile(profile)
        if base_profile == "Observation":
            group_tmp, sub_groups_tmp = get_structure_map_rules(profile, df_questions)
            group_tmp = None
        else:
            group_tmp, sub_groups_tmp = get_structure_map_generated_group(profile, questionnaire_name, df_questions)
        # clean fake/merge
        #replaced = False
        #for group in groups:           
         #   if group.name == group_tmp.name:
          #      #TODO manage group merge ? 
           #     group = group_tmp
            #    replaced = True
             #   out_groups.append(group)
        #      #  break  
        #    elif group.name != 'fake':
        #        out_groups.append(group)
        #if replaced is False:
        #    out_groups.append(group_tmp)
        # subgroup
       # replaced = False
       # for sub_group_tmp in sub_groups_tmp:
       #     for group in groups:     
       #         if group.name == sub_group_tmp.name:
       #             #TODO manage group merge ? 
       #             group = sub_group_tmp
       #             replaced = True
       #             out_groups.append(group)
       #             break  
       #         elif group.name != 'fake':
       #             out_groups.append(group)
       #     if replaced is False:
        if group_tmp is not None :            
            out_groups.append(group_tmp)
        for sub_group_tmp in sub_groups_tmp:
            if sub_group_tmp is not None:            
                out_groups.append(sub_group_tmp)
    return out_groups

def get_structure_map_generated_group(profile, questionnaire_name, df_questions):
    # in case of obsdervation, we need to make at least 1 goup per item
    rules, sub_group = get_structure_map_rules(profile, df_questions)
    group = StructureMapGroup(
        name = clean_group_name(profile)+clean_group_name(questionnaire_name),
        typeMode = Code('types'),
        input = [StructureMapGroupInput(
            mode = Code( 'source'),
            name = "src",
            type = 'questionnaireResponse',
            documentation = questionnaire_name 
        ),
        StructureMapGroupInput(
            mode = Code( 'target'),
            name = "tgt",
            type = clean_group_name(profile)
        )],
        rule = rules
    )
    return group, sub_group

def get_structure_map_rules(profile, df_questions):
    rules = []
    sub_groups = []
    questions = df_questions[df_questions['map_profile'] == profile ].to_dict('index')
    for question_name, question in questions.items():
        rule, sub_group = get_structure_map_rule(question_name,  question)
        if rule is not None:
            rules.append(rule)
        if sub_group is not None:
            sub_groups.append(sub_group)
    return rules, sub_groups

def get_structure_map_rule(question_name, question):
    #TODO manage transform evaluate/create
    # item that have childer item are created then the children rule will create the children Items
    # example rule 13 and 14 http://build.fhir.org/ig/HL7/sdc/StructureMap-SDOHCC-StructureMapHungerVitalSign.json.html
    #profileType, element, valiable = explode_map_resource(question['map_resource'])
    rule = None
    group = None
    #print("Mapping ``{0}`` added".format(fhirmapping))
    if  'map_resource' in question\
        and pd.notna(question['map_resource'])\
        and question['map_resource'] is not None:
        use_helper = str(question['map_resource']).find('::') != -1
        if use_helper:
            helper_array = str(question['map_resource']).split('::')
            helper_func = helper_array[0].strip()
            helper_args = helper_array[1].split('||') if len(helper_array)>1 else []
            fhirmapping = generate_helper(helper_func, 'main', question_name, *helper_args)
            group  = StructureMapGroup(
                name = clean_group_name(question_name),
                typeMode = Code('types'),
                input = [StructureMapGroupInput(
                    mode = Code( 'source'),
                    name = "src",
                    documentation =question_name 
                ),

                StructureMapGroupInput(
                    mode = Code( 'target'),
                    name = "tgt" ,
                    type =       get_base_profile(helper_func)         
                )],
                
                    
                rule = [],
                documentation =generate_helper(helper_func, 'group', question_name, *helper_args)
                )
        else:
            if question['map_resource'].strip()[-1:] != ";":
                question['map_resource'] = question['map_resource'] + " '"+ question_name + "-1';"
            # if variable on root, element is the resource itself
            fhirmapping =  "src.item as item where linkId  = '{0}' -> tgt then {{ item.answer as a -> {1}   }} '{0}-main';".format(
                question_name ,
                question['map_resource']
            )
        
        if fhirmapping is not None:
            fhirmapping = fhirmapping.replace('{{cs_url}}',  get_custom_codesystem_url())
            fhirmapping = fhirmapping.replace('{{canonical_base}}',  get_fhir_cfg().canonicalBase)
 
            rule = StructureMapGroupRule(
                name = question_name,
                source = [StructureMapGroupRuleSource(
                    context = 'item',
                )],
                documentation = fhirmapping,  
                )
    return rule, group

def generate_helper(helper_func, mode, profile, *helper_args):
    return  globals()[helper_func](mode,clean_group_name(profile) , *helper_args )

def SetOfficalGivenName(mode, profile, *args):
    if len(args)!= 3:
        print('Error SetOfficalGivenName{3} must have 3 parameters')
        return None
    if mode == 'main':
        return   "src.item first as item  where linkId =  {0} or linkId =  {1} or linkId =  {2} -> tgt as target,  target.name as name then SetOfficalGivenName{3}(src, name) 'name-main';".format(args[0],args[1],args[2],profile)
    return "group SetOfficalGivenName{3}(source src, target tgt){{\n\
        src -> tgt.use = 'official'  then {{\n\
            src.item as item where linkId  =  {0}   then {{item.answer as a -> tgt.given = a 'f';}} 'first';\n\
            src.item as item  where linkId = {1}   then {{item.answer as a -> tgt.given = a 'm';}} 'middle';\n\
            src.item as item  where linkId = {2}  then {{item.answer as a -> tgt.family = a 'fa';}} 'family';\n\
        }} 'details';\n\
    }}".format(args[0],args[1],args[2],profile)
    

def TransformObservationSelect(mode, profile,canonicalBase = 'http://build.fhir.org',observation='Observation', valueSet = []):
    # check for all valueSet
    return "group TransformObservationSelect(source src: questionnaireResponse, source answerItem, source system, target observation: {{Observation}}, target entry)\n\
    {\n\
    src -> observation.basedOn = src.basedOn; 'careplan'\n\
    answerItem.answer as answer -> observation.value = create('CodeableConcept') as newCC then {\n\
        answer.valueCoding as coding -> newCC.coding = coding as newCoding;\n\
    };\n\
    answerItem.answer as answer then {\n\
        answer.valueCoding as Coding where Coding.code == 'yes' -> observation.status = 'final' 'found';\n\
        answer.valueCoding as Coding where Coding.code == 'no' -> observation.status = 'cancelled' 'not-found';\n\
    } 'status';\n\
  };".replace('{{canonical_base}}', canonicalBase).replace('{{Observation}}', observation)
    
def get_extension_mapping(canonicalBase = 'http://build.fhir.org', extension = 'Extension'):
    return "group setExtension{{extension}}( source src, target tgt) {\n\
        src -> tgt.extension = create('Extension') as ext then {\n\
            src.answer as a -> ext.url = '{{canonical_base}}Extension/{{extension}}', ext.value = a.value 'set-value';\n\
        }\n\
    }".replace('{{canonical_base}}', canonicalBase).replace('{{extension}}', extension)
    
    
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
        group_buffer += get_group_bundle_uid(structure_map.group)
        group_buffer += get_groups_bundle(structure_map.group)
        group_buffer += "\t}'gen-ids';\n"
        group_buffer += "}\n\n"
    for group in structure_map.group:
        if len(group.rule) > 0:
            group_buffer += get_mapping_file_group(group)
        elif group.documentation is not None:
            group_buffer += group.documentation + "\n\n"
    return group_buffer

def get_group_bundle_header():
    return """
group bundleMapping(source src : questionnaireResponse, target bundle : Bundle) {
    src -> bundle.id = uuid() 'id';
    src -> bundle.type = 'batch' 'type';
    """

def get_group_bundle_uid(groups):
    ret =  " src -> "
    for group in groups:
        if group is not None :
            ret_group = get_group_uid(group)
            if ret_group is not None:
                ret += ret_group
    return ret[:-1]+ " then {"
        
def get_group_uid(group):     
    if group is not None and group.name is not None:
        profile = None
        for in_output in group.input:
            if in_output.mode == 'target':
                    profile = in_output.type
        if profile is not None:
            return "uuid() as {}id,".format(group.name)
    
def get_groups_bundle(groups):
    group_buffer =''
    for group in groups:
        cur_group = get_group_bundle(group)
        if cur_group is not None:
            group_buffer += cur_group
    return group_buffer


def get_group_bundle(group):
    profile = None
    question_name = None
    for in_output in group.input:
        if in_output.mode == 'target':
            profile = in_output.type
        if in_output.mode == 'source':
            question_name = in_output.documentation
    if profile is not None and question_name is not None:
        base_profile = get_base_profile(profile)
        action = "create('{0}') as tgt then ".format(get_resource_url('StructureDefinition', profile))
        if base_profile == "Observation":
            action +=  '{'+SetObservation('bundle', profile, group.name) + "'obs-rule';} "
        else:
            action += "{0}group(src, tgt, {0}id)".format(group.name)
    # group name is the clean profile name so  get_base_profile should work
        rule = """
        src -> 
            bundle.entry as entry,
            entry.fullUrl = append("urn:uuid:",{0}id), 
            entry.request as request, 
            request.method = "PUT", 
            request.url = append("{1}/", {0}id),
            entry.resource = {2} '{0}grouprule';
            """.format(
            group.name,
            get_base_profile(group.name),
            action
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
    
    group_buffer =  group_buffer + ",  source resid ) {\n"
    # write Items subsection
    group_buffer += "src -> tgt.id = resid , tgt.meta = create('Meta') as newMeta, newMeta.profile = '{0}' 'set-uuid';\n".format(get_resource_url('StructureDefinition',target))
    if group.rule is not None and group.rule != [] :
        
        # write item mapping
        for rule in group.rule:
            if rule.documentation is not None\
            and rule.name is not None:
                group_buffer = group_buffer + "\t\t" +  str(rule.documentation) +  "\n"
 
    # close group
    group_buffer = group_buffer + "} \n\n"
        
    
    return group_buffer

#ObservationDefinition::'EmCare.B6.DE01'||Quantity
def SetObservation(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    if mode == 'bundle':
        return   "src.item first as item  where linkId =  '{0}' -> item.answer as a then SetObservation{1}(src, a, tgt , {1}id) ".format(args[0], clean_group_name(args[0]))
    elif mode == 'group':
        return """
group SetObservation{2}(source src, source a, target tgt, source oid ){{

    oid ->  tgt.id = oid,
            tgt.identifier = create('Identifier') as CodeID, 
            CodeID.system = 'http://hl7.org/fhir/namingsystem-identifier-type',
            CodeID.use =  'official',
            CodeID.value = 'uuid',
            CodeID.id = oid
            'set-id';
    src -> 
        tgt.basedOn = src.basedOn,
        tgt.encounter = src.encounter,
        tgt. subject = src. subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{3}',
        tgt.status = 'final',
        tgt.code = create('CodeableConcept') as concept, 
            concept.system = '{1}',
            concept.code = '{0}' 'set-code';  

    a -> tgt.value = a 'set-value'; 
}}
    """.format(args[0],get_custom_codesystem_url(),clean_group_name(args[0]),get_resource_url('StructureDefinition',profile))


def SetObservationYesNo(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    if mode == 'bundle':
        return   "src.item first as item  where linkId =  '{0}' -> tgt as target then SetObservation{2}(src, item.answer, target , {1}id) ".format(args[0], clean_group_name(profile))
    elif mode == 'group':
        return """
group SetObservation{2}(source src, source a, target tgt, source oid ){{
    oid ->  tgt.id = oid,
            tgt.identifier = create('Identifier') as CodeID, 
            CodeID.system = 'http://hl7.org/fhir/namingsystem-identifier-type',
            CodeID.use =  'official',
            CodeID.value = 'uuid',
            CodeID.id = oid
            'set-id';

    src -> tgt.basedOn = src.basedOn,
        tgt.encounter = src.encounter,
        tgt. subject = src. subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{3}',
        tgt.code = create('CodeableConcept') as concept, 
            concept.system = '{1}',
            concept.code = '{0}' 'set-code';  
    
    a  where a.value = 'yes' -> tgt.status = 'final' 'set-final';
    a  where a.value = 'no' -> tgt.status = 'cancelled' 'set-nofound'; 
    
}}
    """.format(args[0],get_custom_codesystem_url(),clean_group_name(args[0]),get_resource_url('StructureDefinition',profile))
#FIXME not doing valuset and no patient
def SetObservationBoolean(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    if mode == 'bundle':
        return   "src.item first as item  where linkId =  '{0}' -> tgt as target then SetObservation{2}(src, item.answer, target , {1}id) ".format(args[0], clean_group_name(profile))
    elif mode == 'group':
        return """
group SetObservation{2}(source src, source a, target tgt, source oid ){{
    oid ->  tgt.id = oid,
            tgt.identifier = create('Identifier') as CodeID, 
            CodeID.system = 'http://hl7.org/fhir/namingsystem-identifier-type',
            CodeID.use =  'official',
            CodeID.value = 'uuid',
            CodeID.id = oid
            'set-id';

    src -> tgt.basedOn = src.basedOn,
        tgt.encounter = src.encounter,
        tgt. subject = src. subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{3}',
        tgt.code = create('CodeableConcept') as concept, 
            concept.system = '{1}',
            concept.code = '{0}' 'set-code';  
    
    a  where a.value = true -> tgt.status = 'final' 'set-final';
    a  where a.value = false -> tgt.status = 'cancelled' 'set-nofound'; 
    
}}
    """.format(args[0],get_custom_codesystem_url(),clean_group_name(args[0]),get_resource_url('StructureDefinition',profile))


