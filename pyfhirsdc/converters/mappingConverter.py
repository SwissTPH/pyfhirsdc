


import re
import pandas as pd

from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import get_structure_map_extension
from pyfhirsdc.converters.utils import clean_group_name, clean_name, get_custom_codesystem_url, get_resource_url
from pyfhirsdc.models.mapping import Mapping, MappingGroup, MappingGroupIO, MappingIO, MappingRule
from pyfhirsdc.serializers.mappingSerializer import write_mapping_file
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

FHIR_BASE_PROFILES = [
    "Patient",
    "RelatedPerson",
    "Encounter",
    "Condition",
    "Observation",
    "QuestionnaireResponse",
    "CommunicationRequest"
]

FHIR_ONELINER_PROFILES = [
    "Condition",
    "Observation",
]


def get_questionnaire_mapping(questionnaire_name, df_questions):
    structure_maps = []
    sm_name = clean_name(questionnaire_name)  
    map_filepath = get_resource_path("StructureMap", sm_name, "map")
    profiles = get_question_profiles(df_questions)
    filepath = get_resource_path(
        "StructureMap", 
        sm_name
    )
    # getting the main group
    
    # we init with the QR and bundle, other source/target will be added later
    mapping = Mapping(
        name  = sm_name ,
        url= get_resource_url("StructureMap", sm_name),
        sources = [MappingIO(
            url =  'http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaireresponse',
            alias = 'questionnaireResponse')],
        targets = [MappingIO(
            url =  'http://hl7.org/fhir/StructureDefinition/Bundle',
            alias = 'Bundle')],
        groups =  get_mapping_groups(questionnaire_name, df_questions)
    )
    for profile in profiles:
        base_profile = get_base_profile(profile)
        mapping.targets.append(MappingIO(
            url = get_resource_url('StructureDefinition',base_profile),
            alias = base_profile
        ))
        mapping.products.append(MappingIO(
            url = get_resource_url('StructureDefinition',clean_group_name(profile)),
            alias = profile
        ))
    # create the SM ressource from HAPI server response
    if mapping.groups and len(mapping.groups)>0:
        structure_map = write_mapping_file(map_filepath, mapping)
        if structure_map is not None:
            structure_maps.append(structure_map)
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
    else:
        print("No mapping found for the questionnaire {0}".format(questionnaire_name))

    return mapping

def get_bundle_group(df_questions):
    return MappingGroup(
        name = 'bundletrans',
        sources = [MappingGroupIO(
            name = 'src',
            type = 'questionnaireResponse'
        )],
        targets = [MappingGroupIO(
            name = 'bundle',
            type = 'Bundle'
        )],
        rules = get_bundle_rules(df_questions)

    )
    
def get_bundle_rules(df_questions):
    profiles = get_question_profiles(df_questions)
    # bassic bundle rules
    rules = [
        MappingRule(expression = "src -> bundle.id = uuid()", name = 'id'),
        MappingRule(expression = "src -> bundle.type = 'batch'", name = 'type'),
    ]
    for profile in profiles:
        rule = None
        if is_oneliner_profile(profile):
            questions =  get_question_profiles_detail(df_questions, profile)
            for question_name, row in questions.items():
                rule = get_post_bundle_profile_rule(profile,question_name, row )
                if rule is not None:
                    rules.append(rule)
        else:
            rule = get_put_bundle_profile_rule(profile)
            if rule is not None:
                rules.append(rule)

    return rules     
        
def get_post_bundle_profile_rule(profile, question_name, row):
    base_profile = get_base_profile(profile)
    action = "create('{0}') as tgt ".format(base_profile)
    if base_profile == "Observation":
        sub_rule =  get_obs_call_rule( question_name, row)
    else:
        sub_rule =  MappingRule(  
            expression = "src -> {0}{1}(src, tgt)".format(profile, question_name),
            name = 'act-{0}'.format(question_name))
    return MappingRule(
        expression =   """
    src -> bundle.entry as entry,
        entry.request as request, 
        request.method = "POST", 
        entry.resource = {0}
    """.format(action),
    name = 'post-{0}'.format(question_name),
    rules = [sub_rule]
    )

def get_obs_call_rule( question_name, row):
    # in case of value observation, an empty 
    return MappingRule( 
        expression = "src.item first as item  where linkId =  '{0}' -> item.answer as a then SetObservation{1}(src, a, tgt) ".format(question_name, clean_group_name(question_name)), 
        name = 'obs-{0}'.format(question_name))


def get_put_bundle_profile_rule(profile):
    rule_name = clean_group_name(profile)
    base_profile = get_base_profile(profile)
    return MappingRule(
        expression =   "src -> bundle.entry as entry",
        name = 'put-{0}'.format(rule_name),
        rules = [
            MappingRule(
                expression = 'src -> entry.fullUrl as fullurl then getFullUrl{0}(src, fullurl)'.format(rule_name),
                name = 'fu{0}'.format(rule_name)),
            MappingRule(
                expression = 'src -> entry.request as request, request.method = "PUT", request.url as url then getUrl{0}(src, url)'.format(rule_name),
                name = 'u{0}'.format(rule_name)),
            MappingRule(
                expression = 'src -> entry.resource = create("{0}") as tgt then {1}(src, tgt)'.format(base_profile, rule_name),
                name = 'c{0}'.format(rule_name),
            )
        ]
    )

    
def get_mapping_groups(questionnaire_name, df_questions):
    profiles = get_question_profiles(df_questions)
    out_groups = [get_bundle_group(df_questions)]
    for profile in profiles:
        if is_oneliner_profile(profile):
            rules, sub_groups_tmp = get_mapping_details(profile, df_questions)
            group_tmp = None
        else:
            group_tmp, sub_groups_tmp = get_mapping_group(profile, questionnaire_name, df_questions)
            sub_groups_tmp += get_ref_groups(profile)
            
        if group_tmp is not None :            
            out_groups.append(group_tmp)
        for sub_group_tmp in sub_groups_tmp:
            if sub_group_tmp is not None:            
                out_groups.append(sub_group_tmp)
    return out_groups

def get_mapping_group(profile, questionnaire_name, df_questions):
    # in case of obsdervation, we need to make at least 1 goup per item
    rules, sub_group = get_mapping_details(profile, df_questions)
    group = MappingGroup(
        name = clean_group_name(profile),
        sources = [MappingGroupIO(
            name = "src",
            type = 'questionnaireResponse',
        )],
        targets = [MappingGroupIO(
            name = "tgt",
            type = get_base_profile(profile)
        )],
        rules = rules,
        note = questionnaire_name 
    )
    return group, sub_group

def get_mapping_details(profile, df_questions):
    rules = []
    groups = []
    questions =  get_question_profiles_detail(df_questions, profile)
    for question_name, question in questions.items():
        rule, group = get_mapping_detail(question_name,  question)
        if rule is not None:
            rules.append(rule)
        if group is not None:
            groups.append(group)
    return rules, groups

def get_mapping_detail(question_name, question):
    #TODO manage transform evaluate/create
    # item that have childen item are created then the children rule will create the children Items
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
            group  =  generate_helper(helper_func, 'group', question_name, *helper_args)
        else:
            if question['map_resource'].strip()[-1:] != ";":
                question['map_resource'] = question['map_resource'] + " '"+ question_name + "-1';"
            # if variable on root, element is the resource itself
            match =  re.search("[ =]*val(?:[^\w]|$)",question['map_resource'])
            
            fhirmapping =  "src.item as item where linkId  = '{0}'  -> tgt then {{ {2} -> {1}   }}".format(
                question_name ,
                question['map_resource'],
                "item.answer first as a, a.value as val" if match is not None else "item.answer as a"
            )
        if fhirmapping is not None:
            fhirmapping = fhirmapping.replace('{{cs_url}}',  get_custom_codesystem_url())
            fhirmapping = fhirmapping.replace('{{canonical_base}}',  get_fhir_cfg().canonicalBase)
            rule = MappingRule(
                name = clean_group_name(question_name),
                expression = fhirmapping,
                )
    return rule, group



 

##### helpers 

def is_oneliner_profile(profile):
    base_profile = get_base_profile(profile)
    if base_profile in FHIR_ONELINER_PROFILES:
        return True


def get_base_profile(profile):
    for base_profile in FHIR_BASE_PROFILES:
        if base_profile.lower() in profile.lower():
            return base_profile
        
def add_mapping_url(resource, mapping):
    resource.extension = get_structure_map_extension(
            resource.extension, 
            mapping.url
            )
    return resource

def get_question_profiles(df_questions):
    profiles = df_questions['map_profile'].dropna().unique()
    return profiles

def get_question_profiles_detail(df_questions, profile):
    return df_questions[df_questions['map_profile'] == profile ].to_dict('index')


def generate_helper(helper_func, mode, profile, *helper_args):
    return  globals()[helper_func](mode,clean_group_name(profile) , *helper_args )        


##### mapping snippet


#ObservationDefinition::'EmCare.B6.DE01'||Quantity
def SetGenericObservation( profile, question_name,spe_rules):
    rule_name = clean_group_name(question_name)
    return MappingGroup (
        name = 'SetObservation' + rule_name,
        sources = [
            MappingGroupIO(name = 'src'), # type questionnaireResponse
            MappingGroupIO(name = 'a')# type questionItem
        ],
        targets = [
            MappingGroupIO(name = 'tgt') # type Observation / emacareObservation
        ],
        rules = [
            get_rand_identifier_rule(rule_name),
            get_obs_meta_rule(profile, question_name, rule_name),
            get_timestamp_rule(rule_name),
            *spe_rules
        ]
    )

        
def get_timestamp_rule(rule_name):
    return MappingRule(
        expression = "src.item as item where linkId  = 'timestamp', item.answer as a -> tgt.issued = a",
        name = 'timestamp-{}'.format(rule_name)
    )

def get_obs_meta_rule(profile, question_name, rule_name):
    return  MappingRule(
        expression = """
    src -> tgt.basedOn = src.basedOn,
        tgt.encounter = src.encounter,
        tgt.subject = src.subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{2}',
        tgt.code = create('CodeableConcept') as concept, 
            concept.system = '{1}',
            concept.code = '{0}'
    """.format(question_name,get_custom_codesystem_url(),get_resource_url('StructureDefinition',profile)),
        name = 'code-{}'.format(rule_name)
    )

def get_rand_identifier_rule(rule_name):
    return MappingRule(
        expression = """
    src -> tgt.identifier = create('Identifier') as CodeID, 
        CodeID.system = 'http://hl7.org/fhir/namingsystem-identifier-type',
        CodeID.use =  'official',
        CodeID.value = 'uuid',
        CodeID.id = uuid()
    """,
        name = 'id-{}'.format(rule_name)
    )
    
def get_obs_value_rules(rule_name):
    return [MappingRule(
        expression = "a   -> tgt.value = a, tgt.status = 'final'",
        name = 'final-{}'.format(rule_name)
    )]

def get_notfound_rules(rule_name):
    return [MappingRule(
        expression = "src -> tgt.status = 'cancelled'",
        name = 'notfound-{}'.format(rule_name)
    )]  


def SetObservation(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        return SetGenericObservation( profile, args[0],get_obs_value_rules(clean_group_name(args[0])))

def SetObservationNotFound(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        return SetGenericObservation( profile, args[0],get_obs_value_rules(get_notfound_rules(args[0])))

def get_obs_yes_no_rules(rule_name):
    return [MappingRule(
        expression = "a  where a.value = 'yes' -> tgt.status = 'final' ",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = " a  where a.value = 'no' -> tgt.status = 'cancelled' ",
        name = 'notfound-{}'.format(rule_name)
    )]
    
def SetObservationYesNo(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        return SetGenericObservation( profile, args[0],get_obs_yes_no_rules(clean_group_name(args[0])))
    
def get_obs_bool_rules(rule_name):
    return [MappingRule(
        expression = "a  where a.value = true -> tgt.status = 'final'",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = "a  where a.value = false -> tgt.status = 'cancelled'",
        name = 'notfound-{}'.format(rule_name)
    )]
    

 
def SetObservationBoolean(mode, profile, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        return SetGenericObservation( profile, args[0],get_obs_bool_rules(clean_group_name(args[0])))


def SetOfficalGivenName(mode, profile, *args):
    if len(args)!= 3:
        print('Error SetOfficalGivenName{3} must have 3 parameters')
        return None
    if mode == 'main':
        return   "src.item first as item  where linkId =  {0} or linkId =  {1} or linkId =  {2} -> tgt as target,  target.name as name then SetOfficalGivenName{3}(src, name)".format(args[0],args[1],args[2],profile)
    rule_name = clean_group_name(profile)
    return MappingGroup(
        name = 'SetOfficalGivenName{}'.format(rule_name),
        sources = [MappingGroupIO(name = 'src')],
        targets = [MappingGroupIO(name = 'tgt')],
        rules = [
            MappingRule(
                name= 'sgn{}'.format(rule_name), 
                expression = "src -> tgt.use = 'official'",
                rules = [
                    MappingRule(
                        name = 'f{}'.format(rule_name),      
                        expression = "src.item as item where linkId  =  {0} -> tgt then {{item.answer as a -> tgt.given = a 'f';}}".format(args[0])
                    ),
                    MappingRule(
                        name = 'm{}'.format(rule_name),      
                        expression = "src.item as item where linkId  =  {0} -> tgt then {{item.answer as a -> tgt.given = a 'f';}}".format(args[1])
                    ),
                    MappingRule(
                        name = 'l{}'.format(rule_name),      
                        expression = "src.item as item where linkId  =  {0} -> tgt then {{item.answer as a -> tgt.family = a 'f';}}".format(args[2])
                    )                   
                ]
            )
        ]
    )

def get_ref_groups(profile):
    base_profile = get_base_profile(profile)
    rule_name= clean_group_name(profile)
    return [
        MappingGroup(
            name = 'getId{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [MappingRule(
                name='i{}'.format(rule_name), 
                expression = "src.item first as item where linkId  =  '{0}id'".format(profile),
                rules = [MappingRule(name='id'+rule_name, expression  ="item.answer first as a, a.value as val ->  ressource = val")])]
        ),
        MappingGroup(
            name = 'getFullUrl{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [MappingRule(
                name='fu{}'.format(rule_name), 
                expression = "src.item first as item where linkId  =  '{0}id'".format(profile),
                rules = [MappingRule(name='fu'+rule_name, expression  ="item.answer first as a, a.value as val ->  ressource = append('urn:uuid:', val)")])]
        ),
        MappingGroup(
            name = 'getUrl{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [MappingRule(
                name='u{}'.format(rule_name), 
                expression = "src.item first as item where linkId  =  '{0}id'".format(profile),
                rules = [MappingRule(name='u'+rule_name, expression  ="item.answer first as a, a.value as val ->  ressource =  append('{0}/', val)".format(base_profile))])]
        )
    ]
