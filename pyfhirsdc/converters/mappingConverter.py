


import os
import re

import pandas as pd

from pyfhirsdc.config import (get_defaut_path, get_dict_df, get_fhir_cfg,
                              get_processor_cfg)
from pyfhirsdc.converters.extensionsConverter import (
    get_questionnaire_library, get_structure_map_extension)
from pyfhirsdc.converters.utils import (clean_group_name, clean_name,
                                        get_custom_codesystem_url,
                                        get_resource_url)
from pyfhirsdc.converters.valueSetConverter import get_valueset_df
from pyfhirsdc.models.mapping import (Mapping, MappingGroup, MappingGroupIO,
                                      MappingIO, MappingRule)
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
    "CommunicationRequest"
]

VAL_REGEX = "[ =]*val(?:[^\w]|$)"

def get_questionnaire_mapping(questionnaire_name, df_questions):
    structure_maps = []
    sm_name = clean_name(questionnaire_name)  
    map_filepath = os.path.join(get_defaut_path("Mapping","mapping") ,sm_name+".map")
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
            for question_id, row in questions.items():
                rule = get_post_bundle_profile_rule(profile,question_id, row )
                if rule is not None:
                    rules.append(rule)
        else:
            rule = get_put_bundle_profile_rule(profile)
            if rule is not None:
                rules.append(rule)

    return rules     
        
def get_post_bundle_profile_rule(profile, question_id, row):
    base_profile = get_base_profile(profile)
    rule_name = clean_group_name(profile)
    if base_profile in ('Patient', 'Encounter') or base_profile in FHIR_ONELINER_PROFILES:
        expression =  "src where src.item.where(linkId='{0}').exists()".format(question_id)
    else:
        expression =  "src where src.item.where(linkId='{0}').exists() and src.item.where(linkId='{1}id').first().answer.exists()".format(question_id, rule_name )
    group_name = clean_group_name(profile+question_id)
    return MappingRule(
        name = rule_name,
        expression = expression,
        rules = [MappingRule(
            name = 'act-{0}'.format(question_id),
            expression = "src -> bundle.entry as entry, entry.request as request, request.method = 'POST', entry.resource = create('{0}') as tgt then {1}(src,tgt)".format(
                base_profile,
                group_name))]
    )
    
        
    


def get_put_bundle_profile_rule(profile):
    rule_name = clean_group_name(profile)
    base_profile = get_base_profile(profile)
    rule =  MappingRule(
        expression = get_rule_entry_expression(base_profile, rule_name) ,
        name = 'put-{0}'.format(rule_name),
        rules = [
            get_request_rule(base_profile, rule_name),
            MappingRule(expression = 'src -> entry.resource = create("{0}") as tgt'.format(base_profile),
                rules = [MappingRule(expression = 'src -> tgt then {0}(src, tgt)'.format(rule_name))] )#,
                #get_id_rule(base_profile,rule_name)] )
        ]
    )
    if  base_profile == 'Encounter':
        rule.rules[1].rules.append(MappingRule(expression = 'src.subject as sub -> tgt.subject = sub'))

    return rule

def get_rule_entry_expression(base_profile, cleanned_profile):
    if base_profile in  ('Patient', 'Encounter'):
        return "src -> bundle.entry as entry"
    else:
        return "src where src.item.where(linkId='{}id').answer.exists()-> bundle.entry as entry".format(cleanned_profile)


def get_request_rule(base_profile, cleanned_profile):
    if base_profile == 'Patient':
       return MappingRule( expression = 'src.subject as subject', 
            rules = [MappingRule(expression = "subject.id as idval -> entry.request as request, request.method = 'PUT', request.url = append('/Patient/',idval)")])
    if base_profile == 'Encounter':
        return MappingRule( expression = 'src.encounter as encounter', 
            rules = [MappingRule(expression = "encounter.id as idval  -> entry.request as request, request.method = 'PUT', request.url = append('/Encounter/',idval)")])
    else:
        return MappingRule(
                expression = "src.item first as item where linkId  =  '{0}id' -> entry.request as request, request.method = 'PUT'".format(cleanned_profile),
                rules = [MappingRule( 
                            expression  ="item.answer first as a ->  request", 
                            rules = [MappingRule(expression="a.value as val ->  request.url = append('/RelatedPerson/', val)")])])
        
       # return MappingRule( expression = 'src -> entry then getFullUrl{0}(src, entry)'.format(group_sufix))
        

def get_id_rule(base_profile, group_sufix):
    if base_profile == 'Patient':
        return MappingRule( expression = 'src.subject as subject', 
            rules = [MappingRule(expression = 'subject.id as idval  -> tgt.id = idval')])
    if base_profile == 'Encounter':
        return MappingRule( expression = 'src.encounter as encounter', 
            rules = [MappingRule(expression = 'encounter.id as idval-> tgt.id = idval')])
    else:
        return MappingRule( expression = 'src -> entry then getId{0}(src, tgt)'.format(group_sufix))
    
    
        
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
            if group.groups is not None:
                group_groups = group.groups
                group.groups = []
                groups += group_groups
            
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
            fhirmapping = generate_helper(helper_func, 'main', question['map_profile'], question_name, *helper_args)
            if fhirmapping is not None:
                fhirmapping= inject_config(fhirmapping)
                rule = MappingRule(
                    name = clean_group_name(question_name),
                    expression = fhirmapping,
                    )
            group  =  generate_helper(helper_func, 'group', question['map_profile'], question_name, *helper_args)

        else:
            rule_name = clean_group_name(question_name)
            if question['map_resource'].strip()[-1:] == ";":
                print("Warning, the map ressource must not end with ;")

            # if variable on root, element is the resource itself
            match =  re.search(VAL_REGEX,question['map_resource'])
            rule = MappingRule(
                    name = rule_name,
                    expression =  "src.item as item where linkId  = '{0}'".format(question_name),
                    rules = [ get_val_rule(rule_name, question['map_resource']) if match else get_ans_rule(rule_name, question['map_resource'])]
                )

    return rule, group


def inject_config(value):
    return value.replace('{{cs_url}}',  get_custom_codesystem_url()).replace('{{canonical_base}}',  get_fhir_cfg().canonicalBase)
 
def get_val_rule(rule_name, expression):
    return MappingRule(
        expression  = "item.answer first as a",
        name = 'a'+rule_name,
        rules = [ MappingRule( 
            expression  = "a.value as val -> {0}".format(inject_config(expression)),
            name = 'a'+rule_name
        )]
    )
def get_ans_rule(rule_name, expression):
    return MappingRule( 
            expression  = "item.answer first as a -> {0}".format(inject_config(expression)),
            name = 'a'+rule_name
    )
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


def generate_helper(helper_func, mode, profile, question_id, *helper_args):
    return  globals()[helper_func](mode,profile , question_id, *helper_args )        



        
def get_timestamp_rule(rule_name):
    return MappingRule(    
                        expression = "src.item as item where linkId  =  'timestamp'",
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.issued = val ')])]
        )


def get_obs_meta_rule(profile, code, rule_name):
    return  [
    MappingRule(expression = "src.encounter as encounter -> tgt.encounter = encounter"),
    MappingRule(
        expression = """
    src.subject as subject -> tgt.subject = subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{2}',
        tgt.code = create('CodeableConcept') as concept, concept.coding = create('Coding') as coding, 
            coding.system = '{1}',
            coding.code = '{0}'
    """.format(code,get_custom_codesystem_url(),get_resource_url('StructureDefinition',profile)),
        name = 'code-{}'.format(rule_name)
    )
    ]

def get_code_obs_meta_rule(profile, rule_name):
    return  MappingRule(
        expression = """
    code -> tgt.basedOn = src.basedOn,
        tgt.encounter = src.encounter,
        tgt.subject = src.subject,
        tgt.meta = create('Meta') as newMeta, newMeta.profile = '{1}',
        tgt.code = create('CodeableConcept') as concept, concept.coding = create('Coding') as coding, 
            coding.system = '{0}',
            coding.code = code

    """.format(get_custom_codesystem_url(),get_resource_url('StructureDefinition',profile)),
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

##### mapping snippet

 ####### SetObservationMultiple :  works only with valueset, will generate an obs for all, cancelled is not selected but for the one with value none   ###### 
# args[0] : valueSet name
def SetObservationMultiple(mode, profile, question_id, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        df = get_valueset_df(args[0], True)
        
        return get_base_obs_muli_group(profile, question_id, df)
        


def get_base_obs_muli_group(profile, question_id, df):
    rule_name = clean_group_name(profile+question_id)
    groups, rules = get_base_obs_muli_rules(profile, question_id, df)
    return MappingGroup(
        name = rule_name,
        sources = [
            MappingGroupIO(name = 'src')], # type questionnaireResponse        
        targets = [
            MappingGroupIO(name = 'tgt') # type Observation / emacareObservation
        ],
        rules = rules,
        groups = groups
    )
    

def get_base_obs_muli_rules(profile, question_id,df):
    rules = []
    groups = []
    
    #src where src.item.where(linkId='EmCare.A.DE16').answer.exists(value.code = 'EmCare.A.DE17')=false -> tgt.gender = 'male' 'emcareade17';
    for index, row in df.iterrows():
        row_id = row['code'] 
        rule_name = clean_group_name( question_id + row_id + 't')
        rules.append(MappingRule(
            name = rule_name,
            expression = "src where src.item.where(linkId='{0}').answer.exists(value.code = '{1}') then {2}(src,tgt)".format(question_id, row_id,rule_name)
        ))
        groups.append(
            set_generic_observation_v2(profile, rule_name, row_id, [MappingRule(expression = "src -> tgt.status = 'final'",name = 'f-{}'.format(row_id))])
        )
        rule_name = clean_group_name( question_id + row_id + 'f')
        rules.append(MappingRule(
            name = rule_name,
            expression = "src where src.item.where(linkId='{0}').answer.exists(value.code = '{1}')=false then {2}(src,tgt)".format(question_id, row_id, rule_name)
        
        ))
        groups.append(
            set_generic_observation_v2(profile, rule_name, row_id, [MappingRule(expression = "src -> tgt.status = 'cancelled'",name = 'f-{}'.format(row_id))])
        )
    return groups, rules
        

def set_generic_observation_v2(profile, rule_name, code ,spe_rules):
    profile = clean_group_name(profile)
    return MappingGroup (
        name = clean_group_name(profile+code),
        sources = [
            MappingGroupIO(name = 'src'), # type questionnaireResponse
        ],
        targets = [
            MappingGroupIO(name = 'tgt') # type Observation / emacareObservation
        ],
        rules = [
            get_rand_identifier_rule(rule_name),
            *get_obs_meta_rule(profile, code, rule_name),
            get_timestamp_rule(rule_name),
            MappingRule(name = 'patient', expression = "src.subject as subject -> tgt.subject = subject "),
            *spe_rules
        ]
    )

            

def get_generic_obs_cancelled_group():
    pass


 ####### SetObservation :  set the value of an observation, obs will never be cancelled  ###### 
 #args[0]: question name
 # 
def SetObservation(mode,  profile, question_id, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        code = args[0] if len(args) == 1 else question_id
        rule_name = clean_group_name(question_id)
        return set_generic_observation_v2( profile, rule_name, code, get_obs_value_rules(code))

def get_obs_value_rules(question_id):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, [MappingRule(
                expression = "a   -> tgt.value = a, tgt.status = 'final'",
                name = 'val-{}'.format(rule_name)
            )])]
            
    
def wrapin_first_answers_rules(rule_name, question_id, rules):
    return MappingRule(
        expression = "src.item first as item  where linkId =  '{}'".format(question_id),
        name = 'it-{}'.format(rule_name),
        rules = [MappingRule(
            expression = "item.answer first as a",
            name = 'an-{}'.format(rule_name),
            rules = rules
        )]
    )

 ####### SetObservationNotFound :  if yes, set the related obs to cancelled  ###### 
 #args[0]: question name 
def SetObservationNotFound(mode, profile, question_id, *args):
    if len(args)> 1:
        print('Error SetObservation must have 1 or 0 parameters')
        return None
    elif mode == 'group':
        code = args[0] if len(args) == 1 else question_id
        rule_name = clean_group_name(question_id)
        return set_generic_observation_v2( profile, rule_name, code,get_obs_value_rules(get_notfound_rules(code)))

def get_notfound_rules(rule_name):
    return [MappingRule(
        expression = "src -> tgt.status = 'cancelled'",
        name = 'notfound-{}'.format(rule_name)
    )]  

 ####### SetObservationYesNo :  set an  observation from yes/no, No result in obs beeing cancelled  ######
  #args[0]: question name
def SetObservationYesNo(mode, profile, question_id, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        code = args[0] if len(args) == 1 else question_id
        rule_name = clean_group_name(question_id)
        return set_generic_observation_v2( profile, rule_name, code, get_obs_yes_no_rules(code))
    

    
def get_obs_yes_no_rules(question_id):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, [MappingRule(
        expression = "a  where a.value = 'yes' -> tgt.status = 'final' ",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = " a  where a.value = 'no' -> tgt.status = 'cancelled' ",
        name = 'notfound-{}'.format(rule_name)
    )])]


 ####### SetObservationBoolean :  set an  observation from boolean, false result in obs beeing cancelled  ###### 
 #args[0]: question name
def SetObservationBoolean(mode, profile, question_id, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    elif mode == 'group':
        code = args[0] if len(args) == 1 else question_id
        rule_name = clean_group_name(question_id)
        return set_generic_observation_v2( profile, rule_name, code,get_obs_bool_rules(code))

def get_obs_bool_rules(question_id):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, [MappingRule(
        expression = "a  where a.value = true -> tgt.status = 'final'",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = "a  where a.value = false -> tgt.status = 'cancelled'",
        name = 'notfound-{}'.format(rule_name)
    )])]

####### SetOfficalGivenNameSetOfficalGivenName :  to have all the name under a single "official" ###### 
#args[0]: question name given
#args[1]: question name mid
#args[2]: question name lasst
def SetOfficalGivenName(mode, profile, question_id, *args):
    rule_name = clean_group_name(profile)
    if len(args)!= 3:
        print('Error SetOfficalGivenName must have 3 parameters')
        return None
    if mode == 'main':
        return   "src.item first as item  where linkId =  '{0}' or linkId =  '{1}' or linkId =  '{2}' -> tgt as target,  target.name as name then SetOfficalGivenName{3}(src, name)".format(args[0],args[1],args[2],rule_name)
    return MappingGroup(
        name = 'SetOfficalGivenName{}'.format(rule_name),
        sources = [MappingGroupIO(name = 'src')],
        targets = [MappingGroupIO(name = 'tgt')],
        rules = [
            MappingRule(
                expression = "src -> tgt.use = 'official'",
                rules = [
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[0]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.given = val ')])]
                    ),
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[1]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.given = val ')])]
                    ),
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[2]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.family = val ')])]
                    )

   
                ]
            )
        ]
    )

####### SetOfficalGivenNameSetOfficalGivenName :  to have all the name under a single "official" ###### 
#args[0]: question name given
#args[1]: question name mid
#args[2]: question name lasst
def SetOfficalGivenName(mode, profile, question_id, *args):
    rule_name = clean_group_name(profile)
    if len(args)!= 3:
        print('Error SetOfficalGivenName must have 3 parameters')
        return None
    if mode == 'main':
        return   "src.item first as item  where linkId =  '{0}' or linkId =  '{1}' or linkId =  '{2}' -> tgt as target,  target.name as name then SetOfficalGivenName{3}(src, name)".format(args[0],args[1],args[2],rule_name)
    return MappingGroup(
        name = 'SetOfficalGivenName{}'.format(rule_name),
        sources = [MappingGroupIO(name = 'src')],
        targets = [MappingGroupIO(name = 'tgt')],
        rules = [
            MappingRule(
                expression = "src -> tgt.use = 'official'",
                rules = [
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[0]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.given = val ')])]
                    ),
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[1]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.given = val ')])]
                    ),
                    MappingRule(    
                        expression = "src.item as item where linkId  =  '{0}'".format(args[2]),
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> tgt.family = val ')])]
                    )

   
                ]
            )
        ]
    )

####### SetOfficalGivenNameSetOfficalGivenName :  to have all the name under a single "official" ###### 
#args[0]: days
#args[1]: month
#args[2]: years
def SetDoBFromPart(mode, profile, question_id, *args):
    rule_name = clean_group_name(profile)
    if len(args)!= 3:
        print('Error SetDoBFromPart must have 3 parameters')
        return None
    if mode == 'main':
        return   "src.item first as item  where linkId =  '{0}' or linkId =  '{1}' or linkId =  '{2}' -> tgt as target,  target.name as name then SetDoBFromPart{3}(src, name)".format(args[0],args[1],args[2],rule_name)
    return MappingGroup(
        name = 'SetDoBFromPart{}'.format(rule_name),
        sources = [MappingGroupIO(name = 'src')],
        targets = [MappingGroupIO(name = 'tgt')],
        groups=[
            MappingGroup(
            name = 'SetDoBFromPartD{}'.format(rule_name),        
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                MappingRule(
                expression = "src.item as itemD where linkId  =  {0}".format(args[0])
                )
            ]
            ),
            MappingGroup(name = 'SetDoBFromPartM{}'.format(rule_name),        
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                MappingRule(
                expression = "src.item as itemM where linkId  =  {0}".format(args[1])
                )
            ]
            ),
            MappingGroup(name = 'SetDoBFromPartY{}'.format(rule_name),     
            sources = [MappingGroupIO(name = 'src'),MappingGroupIO(name = 'itemD'),MappingGroupIO(name = 'itemM')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                MappingRule(
                expression = "src.item as itemY where linkId  =  {0}".format(args[2],
                rules = [
                    MappingRule(expression = '(((now() - (itemD + "days")) - itemM + "months") - itemY + "years"', 
                        rules = [
                            MappingRule(expression = ' -> tgt.birthDate = val ')])])
                )
            ]
            )
            ]
    )
    

####### MapValueSetExtCode :  to avoid concept maps when the system is predefined ###### 
#args[0]: valueset
#args[1]: path to map
def MapValueSetExtCode(mode, profile,question_id, *args):
    rule_name = clean_group_name(question_id)
    if mode == 'main':
        return   "src.item as item where linkId =  '{0}' then {{ item.answer first as a then MapValueSetExtCode{1}(a, tgt) '{1}d'; }}".format(question_id,rule_name)
    if len(args)!= 2:
        print('Error SetOfficalGivenName must have 2 parameters, valueset name and mappath')
    # get Value set df
    maprules = get_valueset_map_source(args[0], args[1])
    if maprules is not None:
        return MappingGroup(
            name = 'MapValueSetExtCode{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                MappingRule(
                    expression = "src -> tgt",
                    rules = [maprules]
                )
            ]
        )

def get_valueset_map_source(valueset_name, map_path):
    sub_rules = []
    df = get_valueset_df(valueset_name, True)
    if df is not None:
        map_path_list =  get_map_path_list(map_path)
        for index, row in df.iterrows():
            if pd.notna(row['map_concept'])  :
                map_concepts = row['map_concept'].split('||')
                for mapping in map_concepts:
                    mapping_details = mapping.split('::')
                    if len(mapping_details)-1>0:
                        to_code = mapping_details[len(mapping_details)-1]
                        sub_rules.append(MappingRule(
                                expression = "src where value.code = '{0}' -> {1} = '{2}'".format(row['code'],map_path_list[len(map_path_list)-1] ,to_code)
                            ))
        return get_map_path_rule(map_path_list, sub_rules)
        



####### WalkMap :  to avoid concept maps when the system is predefined ###### 
#args[0]: path to map " assing ex " parent.childlvl1.childlvl2 = val
def MapWalk(mode, profile, question_id,*args):
    # TODO support slicing and create
    val_a = "val" if  re.search(VAL_REGEX,args[0]) else "a"
    rule_name = clean_group_name(question_id)
    if mode == 'main':
        if val_a == 'val':
            return   "src.item as item where linkId =  '{0}' then {{ item.answer first as a then {{ a.value as val then MapWalk{1}(val, tgt) '{1}d'; }} '{1}dval'; }}".format(profile,rule_name)
        else:
            return   "src.item as item where linkId =  '{0}' then {{ item.answer first as a then MapWalk{1}(a, tgt) '{1}d'; }}".format(question_id,rule_name)
    if len(args)!= 1:
        print('Error MapWalk must have 1 parameters, valueset name and mappath')
    # get Value set df
    map_path_list =  get_map_path_list(args[0])
    
    rules = MappingRule(
        name = 'asgn',
        expression = map_path_list[-1]
        ) 
    map_path_list = map_path_list[:-1]
    return MappingGroup(
            name = 'MapWalk{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [get_map_path_rule(map_path_list, rules, val_a)]
        )

def get_map_path_list(map_path):
    map_path_list = map_path.split('.')
    # merge the last 2 element
    if len(map_path_list)>1:
        map_path_list[len(map_path_list)-2] = '.'.join(map_path_list[-2:])
        map_path_list.pop()
    return map_path_list

def get_map_path_rule(map_path_list, rules, src_name = "src"):
    if len(rules) == 0 or len(map_path_list) == 0 :
        return None
    elif len(map_path_list) == 1:
        if len(rules) == 1:
            return rules[0]
        else:
            last_map = map_path_list[0].split('.')[0]
            return MappingRule(
                name = "mapbase",
                expression = "{0} -> {1}".format(src_name,last_map),
                rules = rules
            )
    else:
        return MappingRule(
                name = "map"+len(map_path_list),
                expression = "{0} -> {1}.{2} as {2}".format(src_name, map_path_list[0],map_path_list[1]),
                rules = [get_map_path_rule(map_path_list[1:], rules)]
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
                expression = "src.item first as item where linkId  =  '{0}id' -> tgt".format(rule_name),
                rules = [MappingRule(
                    expression  ="item.answer first as a ->  tgt ", 
                        rules = [MappingRule(expression="a.value as val ->  tgt.id = val")])])]
        ),
        MappingGroup(
            name = 'getFullUrl{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [MappingRule( 
                expression = "src.item first as item where linkId  =  '{0}id' -> tgt".format(rule_name),
                rules = [MappingRule(expression  ="item.answer first as a -> tgt", 
                        rules = [MappingRule(expression="a.value as val ->  tgt.fullUrl = append('urn:uuid:', val)")])])]
        ),
        MappingGroup(
            name = 'getUrl{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [MappingRule(
                expression = "src.item first as item where linkId  =  '{0}id' -> tgt".format(rule_name),
                rules = [MappingRule( 
                            expression  ="item.answer first as a ->  tgt", 
                            rules = [MappingRule(expression="a.value as val ->  ref.reference = append('/{0}/', val)".format(base_profile))])])]
        )
    ]

### create related person
# args[0] linkid for relatedPerson
# args[1]  reference of PD 
def SetCommunicationRequest(mode, profile, question_id,*args):
    rule_name = clean_group_name(profile+question_id)
    id_prefix = clean_group_name(profile)
    if mode == 'main':
        return  None
    elif mode == 'group':
        
        return MappingGroup(
            name = rule_name,
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                #MappingRule(name = 'cat', expression = "src -> tgt.category = cc('http://terminology.hl7.org/CodeSystem/communication-category', 'notification')"),
                MappingRule(expression = "src ->  tgt.category = create('CodeableConcept') as cc, cc.coding = create('Coding') as c, c.system ='http://hl7.org/fhir/ValueSet/communication-category', c.code = 'notification'"),
                #MappingRule(name = 'pd', expression = "src -> tgt.status = 'active', tgt.basedOn = src.basedOn".format( inject_config(args[0]))),
                MappingRule(name = 'quest', expression = "src.questionnaire as q ->   tgt.about = create('Reference') as ref, ref.type ='Questionnaire', ref.reference = q"),
                MappingRule(expression = "src.subject as subject ->   tgt.subject = subject "),
                MappingRule(expression = "src ->   tgt.recipient =create('Reference') as ref ",
                    rules = [
                        MappingRule( expression = "src -> ref.type = 'RelatedPerson'" ),
                        MappingRule(
                expression = "src.item first as item where linkId  =  '{0}' -> tgt".format(args[0]),
                rules = [MappingRule( 
                            expression  ="item.answer first as a ->  tgt", 
                            rules = [MappingRule(expression="a.value as val ->  ref.reference = append('/RelatedPerson/', val)")])])
                    ])
                
            ]
    )    

### create related person
# args[0] linkid for relatedPerson
# args[1] linkid for patient
# args[2] linkid relationship
  
def SetRelatedPerson():
    pass