


import os
import re

import pandas as pd

from pyfhirsdc.config import get_defaut_path, get_fhir_cfg, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import \
    get_structure_map_extension
from pyfhirsdc.converters.utils import (clean_group_name, clean_name,
                                        get_custom_codesystem_url, get_fpath,
                                        get_resource_url, inject_config)
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
    "CommunicationRequest",
]

VAL_REGEX = "[ =]*val(?:[^\w]|$)"


# get the profiles used
# generate the mapping, fill it wil the groups
# 
def get_questionnaire_mapping(questionnaire_name, df_questions_item):
    sm_name = clean_name(questionnaire_name)  
    map_filepath = os.path.join(get_defaut_path("Mapping","mapping") ,sm_name+".map")
    profiles = get_questions_profiles(df_questions_item)
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
        groups =  get_mapping_groups(questionnaire_name, df_questions_item)
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
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
    else:
        print("No mapping found for the questionnaire {0}".format(questionnaire_name))

    return mapping



def get_bundle_group(df_questions_item):
    profiles = get_questions_profiles(df_questions_item)

    # bassic bundle rules
    rules = [
        MappingRule(expression = "src -> bundle.id = uuid()", name = 'id'),
        MappingRule(expression = "src -> bundle.type = 'batch'", name = 'type'),
    ]
    for profile in profiles:
        base_profile = get_base_profile(profile)
        if is_oneliner_profile(profile):
            questions =  get_profiles_quesitons(df_questions_item, profile)
            for question in questions.values():
                q_rules = get_post_oneliner_bundle_profile_rule(profile,question, df_questions_item )
                if q_rules is not None:
                    rules += q_rules
        elif base_profile in ('Patient', 'Encounter'):
            rule = get_put_bundle_profile_rule(profile,df_questions_item)
            if rule is not None:
                rules.append(rule)
        else:
            rule = get_post_bundle_profile_rule(profile, df_questions_item )
            if rule is not None:
                rules.append(rule)

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
        rules = rules

    )


# this function create as many ressource as get_helper 'rules' function returns rules
def get_post_oneliner_bundle_profile_rule(profile,question,df_questions_item):
    
    rule_name = clean_group_name(profile+question['id'])

    main_rules = None
    helper_func, helper_args= get_helper(question)
    # get main rules from helper
    if helper_func is not None:
        main_rules = generate_helper(helper_func, 'rules', profile, question['id'],df_questions_item, *helper_args)
    # use default
    if main_rules is None:
        main_rules = [
            MappingRule(expression  ='src -> tgt then {0}(src, tgt)'.format(rule_name))
                # get_id_rule(base_profile,rule_name)
            ]

    # if there is only one rule then use the std
    if len(main_rules) == 1:
          rules= [
            wrapin_entry_create(profile,question['id'],df_questions_item, main_rules)
          ]
    # several rules will be generated therefore the condition for entry creation won't be reduced to wrapin_fpath
    elif main_rules is not None:
         rules = main_rules
    return rules


def wrapin_entry_create(profile,question_id,df_questions_item, rules):
    base_profile = get_base_profile(profile)
    return wrapin_fpath(["{0}".format(question_id)],df_questions_item,[
                    MappingRule(expression = "src -> bundle.entry as entry ",
                    rules = [
                        MappingRule(expression = "src -> entry.request as request, request.method = 'POST' , uuid() as uuid, request.url = append('/{}/', uuid)".format(base_profile)),
                        MappingRule(
                            expression = "src -> entry.resource = create('{0}') as tgt".format(base_profile),
                            rules = rules
                )])])


def get_post_bundle_profile_rule(profile,df_questions_item):
    rule_name = clean_group_name(profile)
    base_profile = get_base_profile(profile)
            
    rule =   wrapin_fpath(["{0}id".format(rule_name)],df_questions_item,[
                MappingRule(
                expression = "src -> bundle.entry as entry ,entry.request as request, request.method = 'POST' , entry.resource = create('{0}') as tgt".format(base_profile),
                rules = [
                    MappingRule(expression  ='src -> tgt then {0}(src, tgt)'.format(rule_name)),
                    MappingRule(expression  ='item.answer first as a',
                                rules = [ MappingRule(expression="a.value as val -> request.url = append('/{0}/', val)".format(base_profile))])
                    
                         # get_id_rule(base_profile,rule_name)
                        ]
            )])
    
    return rule
        

 
def get_test_fpaths(linkid,df_questions,rules):
    pass
    
def wrapin_fpath(fpaths,df_questions,rules):
    a_ids = fpaths.pop(0).split('||')
    linkid=a_ids[0]
    # if on the leaf there is several id, only the parent of the first will be taken
    fpaths = get_fpath(df_questions,linkid, fpaths)
    leaf_rule = None
    fpaths_len = len(fpaths)
    if fpaths_len==1:
        return MappingRule(
            expression = "src.item first as item  where linkId = '{}'".format("' or linkId= '".join(a_ids)),
            rules = rules
        )
    else:
        # we trust the content of a_ids and remove the result from get_fpath
        fpaths.pop(0)
        leaf_rule = MappingRule(
            expression = "itm{}.item first as item  where linkId =  '{}'".format(len(fpaths),"' or linkId= '".join(a_ids)),
            rules = rules
        )
        while len(fpaths)>0:
            fpath = fpaths.pop(0)
            itm_name = "src" if len(fpaths) == 0 else "itm{}".format(len(fpaths)) 
            leaf_rule = MappingRule(
                expression = "{}.item first as itm{}  where linkId =  '{}'".format(itm_name, len(fpaths)+1,fpath),
                rules = [leaf_rule]
            )
    return leaf_rule


def get_put_bundle_profile_rule(profile,df_questions_item):
    rule_name = clean_group_name(profile)
    base_profile = get_base_profile(profile)
    
    rule =  MappingRule(
        expression = "src -> bundle.entry as entry" ,
        name = 'put-{0}'.format(rule_name),
        rules = [
            get_request_rule(base_profile, rule_name,df_questions_item),
            MappingRule(expression = 'src ->  entry.resource = create("{0}") as tgt'.format(base_profile),
                rules = [MappingRule(expression = 'src -> tgt then {0}(src, tgt)'.format(rule_name)),
                ] ) # get_id_rule(base_profile,rule_name)
        ]
    )
    if  base_profile == 'Encounter':
        rule.rules[1].rules.append(MappingRule(expression = 'src.subject as sub -> tgt.subject = sub'))

    return rule



def get_request_rule(base_profile, cleanned_profile, df_questions_item):
    if base_profile == 'Patient':
       return MappingRule( expression = 'src.subject as subject', 
            rules = [MappingRule(expression = "subject.id as idval -> entry.request as request, request.method = 'PUT', request.url = append('/Patient/',idval)")])
    if base_profile == 'Encounter':
        return MappingRule( expression = 'src.encounter as encounter', 
            rules = [MappingRule(expression = "encounter.id as idval  -> entry.request as request, request.method = 'PUT', request.url = append('/Encounter/',idval)")])
    else:
        # id issue on the android SDK prevent the PUT / reuse of id 
        return wrapin_fpath(["{0}id".format(cleanned_profile)],df_questions_item,[MappingRule(
                expression = "src -> entry.request as request, request.method = 'PUT'",
                rules = [MappingRule( 
                            expression  ="item.answer first as a ->  request", 
                            rules = [MappingRule(expression="a.value as val ->  request.url = append('/{}/', val)".format(base_profile))]),
                         ])
        ])
        
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
    

# called by get_questionnaire_mapping    
def get_mapping_groups(questionnaire_name, df_questions_item):
    profiles = get_questions_profiles(df_questions_item)
    out_groups = [get_bundle_group(df_questions_item)]
    for profile in profiles:
        if is_oneliner_profile(profile):
            rules, groups = get_mapping_details(profile, df_questions_item)
        else:
            groups = get_mapping_group(profile, questionnaire_name, df_questions_item)
            #sub_groups_tmp += get_ref_groups(profile)          
        if groups is not None :            
            out_groups+= groups
    return out_groups

def get_mapping_group(profile, questionnaire_name, df_questions_item):
    # in case of obsdervation, we need to make at least 1 goup per item
    rules, groups = get_mapping_details(profile, df_questions_item)
    
    if groups is None:
        groups = []
    
    groups.append( MappingGroup(
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
    )
    
    return groups

def get_mapping_details(profile, df_questions_item):
    rules = []
    groups = []
    questions =  get_profiles_quesitons(df_questions_item, profile)
    for question in questions.values():
        q_rules, q_groups = get_mapping_detail(question['id'],  question,  df_questions_item)
        if q_rules is not None:
            rules+=q_rules
        if q_groups is not None:
            for g in q_groups:
                if isinstance(g,list):
                    groups+=g
                elif  isinstance(g,MappingGroup):
                    groups.append(g)
                else:
                    pass
            
            #if group.groups is not None:
            #    group_groups = group.groups
            #    group.groups = []
            #    groups += group_groups
            
    return rules, groups

def get_helper(question):
    helper_func = None
    helper_args = []
    if 'map_resource' in question and pd.notna(question['map_resource']):
        helper_array = str(question['map_resource']).split('::')
        helper_func = helper_array[0].strip()
        # quite if not helper is found
        if " " in helper_func.strip() or  helper_func not in globals():
            return None, None
        if len(helper_array)>1:
            helper_args = [x.strip() for x in helper_array[1].split('||')] if len(helper_array)>1 else []
    return helper_func, helper_args

    


def get_mapping_detail(question_name, question, df_questions_item):
    #TODO manage transform evaluate/create
    # item that have childen item are created then the children rule will create the children Items
    # example rule 13 and 14 http://build.fhir.org/ig/HL7/sdc/StructureMap-SDOHCC-StructureMapHungerVitalSign.json.html
    #profileType, element, valiable = explode_map_resource(question['map_resource'])
    rules = None
    groups = None
    #print("Mapping ``{0}`` added".format(fhirmapping))wrapin_entry_create(profile,question,df_questions_item, rules)
    if  'map_resource' in question\
        and pd.notna(question['map_resource'])\
        and question['map_resource'] is not None:
        
        helper_func ,helper_args = get_helper(question)
        if helper_func is not None:
            rules = generate_helper(helper_func, 'rules', question['map_profile'], question_name, df_questions_item ,*helper_args)
            groups  =  generate_helper(helper_func, 'groups', question['map_profile'], question_name,df_questions_item, *helper_args)

        else:
            rule_name = clean_group_name(question_name)
            if question['map_resource'].strip()[-1:] == ";":
                print("Warning, the map ressource must not end with ;")

            # if variable on root, element is the resource itself
            match =  re.search(VAL_REGEX,question['map_resource'])
            rules = [
                wrapin_fpath([question_name],
                    df_questions_item,
                    [ get_val_rule(rule_name, question['map_resource']) if match else get_ans_rule(rule_name, question['map_resource'])]
                )
            ]

    return rules, groups



 
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


def get_questions_profiles(df_questions):
    profiles = df_questions['map_profile'].dropna().unique()
    return profiles

def get_profiles_quesitons(df_questions, profile):
    return df_questions[df_questions['map_profile'] == profile ].to_dict('index')


def generate_helper(helper_func, mode, profile, question_id,df_questions, *helper_args):
    return  globals()[helper_func](mode,profile , question_id,df_questions, *helper_args )        



        
def get_timestamp_rule( target = 'tgt.issued' ):
    return MappingRule(    
                        expression = "src.item as item where linkId  =  'timestamp'",
                        rules = [
                            MappingRule(expression = 'item.answer first as a',
                                rules = [MappingRule(expression = 'a.value as val -> {} = val '.format(target))])]
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
def SetObservationMultiple(mode, profile, question_id, df_questions, *args):
    if len(args)!= 1:
        print('Error SetObservation must have 1 parameters')
        return None
    df_valueset = get_valueset_df(args[0], True)   
    if mode == 'rules':
        return get_base_obs_muli_rules(profile, question_id,df_questions,df_valueset)
    elif mode == 'groups':
        return get_base_obs_muli_groups(profile, question_id,df_valueset)
        

def get_base_obs_muli_rules(profile, question_id,df_questions,df_valueset):
    rules = []
 
    
    #src where src.item.where(linkId='EmCare.A.DE16').answer.exists(value.code = 'EmCare.A.DE17')=false -> tgt.gender = 'male' 'emcareade17';
    for index, row in df_valueset.iterrows():
        if "map" in row and   pd.notna(row["map"]) and row['map'].lower().startswith('obs'):
            row_id = row['code']
            code  =question_id+ "&" +  row_id
            rule_name = clean_group_name( profile + code + 't')
            rules.append(MappingRule(
                expression = "src where src.item.where(linkId='{0}').answer.where(value.code = '{1}') ".format(question_id, row_id),
                rules = [wrapin_entry_create( profile, question_id,df_questions,[MappingRule(expression = 'src then {}(src,tgt)'.format(rule_name) )])]
            ))
            
            rule_name = clean_group_name( profile + code+ 'f')
            rules.append(MappingRule(
                expression = "src where src.item.where(linkId='{0}').exists() and src.item.where(linkId='{0}').answer.where(value.code = '{1}').empty()  ".format(question_id, row_id),
                rules = [wrapin_entry_create(profile, question_id,df_questions, [MappingRule(expression = 'src then {}(src,tgt)'.format(rule_name) )])]
            ))
            
    return  rules


def get_base_obs_muli_groups(profile, question_id,df):
    groups = []
    
    #src where src.item.where(linkId='EmCare.A.DE16').answer.exists(value.code = 'EmCare.A.DE17')=false -> tgt.gender = 'male' 'emcareade17';
    for index, row in df.iterrows():
        if "map" in row and   pd.notna(row["map"]) and row['map'].lower().startswith('obs'):
            row_id = row['code']
            code  =question_id+ "&" +  row_id
            rule_name = clean_group_name( profile + code + 't')
            groups.append(
                set_generic_observation_v2(profile, rule_name, code, [MappingRule(expression = "src -> tgt.status = 'final', tgt.value = true")],'t')
            )
            rule_name = clean_group_name( profile + code+ 'f')
            groups.append(
                set_generic_observation_v2(profile, rule_name, code, [MappingRule(expression = "src -> tgt.status = 'cancelled',tgt.value = false",)],'f')
            )
    return groups        

def set_generic_observation_v2(profile, rule_name, code ,spe_rules, sufix = ''):
    profile = clean_group_name(profile)
    return MappingGroup (
        name = clean_group_name(profile+code+sufix),
        sources = [
            MappingGroupIO(name = 'src'), # type questionnaireResponse
        ],
        targets = [
            MappingGroupIO(name = 'tgt') # type Observation / emacareObservation
        ],
        rules = [
            get_rand_identifier_rule(rule_name),
            *get_obs_meta_rule(profile, code, rule_name),
            get_timestamp_rule(),
            MappingRule(name = 'patient', expression = "src.subject as subject -> tgt.subject = subject "),
            *spe_rules
        ]
    )

            

def get_generic_obs_cancelled_group():
    pass


 ####### SetObservation :  set the value of an observation, obs will never be cancelled  ###### 
 #args[0]: question name
 #args[1]: none name
 # 
def SetObservationCode(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        none_name = args[1] if len(args)>1 else 'none'
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code, get_obs_value_rules(code,df_questions_item, none_name))]

def get_obs_value_rules(question_id, df_questions_item,none_name):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a.value as val",
    rules = [MappingRule(
        expression = "val where val.code = '{}' -> tgt.status = 'cancelled',tgt.value = false ".format(none_name),
    ), MappingRule(
        expression="val where val.code != '{}' -> tgt.value = create('CodeableConcept') as cc, cc.coding = val, tgt.status = 'final'"
    )])])]
            
    
def wrapin_first_answers_rules(rule_name, question_id,df_questions_item, rules):
    return wrapin_fpath([question_id],df_questions_item,[MappingRule(
            expression = "item.answer first as a",
            rules = rules
        )]
    )



def SetObservation(mode,  profile, question_id,df_questions_item, *args):
     SetObservationQuantity(mode,  profile, question_id,df_questions_item, *args)   
####### SetObservationQuantity :  set the value of an observation, obs will never be cancelled; Same
####### SetObservation but now accounting that the answer won't be the value itself
####### but will hold the value in the field value of Quantity  ###### 
 #args[0]: question name
 # 
def SetObservationQuantity(mode,  profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        code = question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code, get_obs_qty_value_rules(code,df_questions_item))]

def get_obs_qty_value_rules(question_id,df_questions_item):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item, [MappingRule(
                expression = "a.value as val -> tgt.value = val, tgt.status = 'final'"
            )])]

 ####### SetObservationNotFound :  if yes, set the related obs to cancelled  ###### 
 #args[0]: question name 
def SetObservationNotFound(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        code = question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code,get_obs_value_rules(get_notfound_rules(code,question_id, df_questions_item)))]

def get_notfound_rules(rule_name,question_id, df_questions_item):
    return [wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "src -> tgt.status = 'cancelled',tgt.value = true",
        name = 'notfound-{}'.format(rule_name)
    )] )] 

 ####### SetObservationYesNo :  set an  observation from yes/no, No result in obs beeing cancelled  ######
  #args[0]: question name
def SetObservationYesNo(mode, profile, question_id,df_questions_item, *args):

    if mode == 'groups':
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code, get_obs_yes_no_rules(code,df_questions_item))]
    

    
def get_obs_yes_no_rules(question_id,df_questions_item,):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a  where a.value = 'yes' -> tgt.status = 'final', tgt.value = true ",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = " a  where a.value = 'no' -> tgt.status = 'cancelled' , tgt.value = false",
        name = 'notfound-{}'.format(rule_name)
    )])]
    

 ####### SetObservationBoolean :  set an  observation from boolean, false result in obs beeing cancelled  ###### 
 #args[0]: question name
def SetObservationBoolean(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code,get_obs_bool_rules(code, df_questions_item))]

def get_obs_bool_rules(question_id, df_questions_item):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a  where a.value = true -> tgt.status = 'final', tgt.value = true",
        name = 'final-{}'.format(rule_name)
    ),MappingRule(
        expression = "a  where a.value = false -> tgt.status = 'cancelled', tgt.value = false",
        name = 'notfound-{}'.format(rule_name)
    )])]

 ####### SetObservationBoolean :  set an  observation from boolean, false result in obs beeing cancelled  ###### 
 #args[0]: question name
def SetObservationCodeBoolean(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code,get_obs_bool_code_rules(code, df_questions_item))]

def get_obs_bool_code_rules(question_id, df_questions_item):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a.value as val",
    rules = [MappingRule(
        expression = "val where val.code = 'true' -> tgt.status = 'final',tgt.value = true ",
    )])])]
            

####### SetOfficalGivenNameSetOfficalGivenName :  to have all the name under a single "official" ###### 
#args[0]: question name last
#args[1]: question name first
#args[2]: question name mid
def SetOfficalGivenName(mode, profile, question_id,df_questions_item, *args):
    rule_name = clean_group_name(profile)
    if len(args)< 2:
        print('Error SetOfficalGivenName must have 3 parameters')
        return None
    if mode == 'rules':
        return [
            wrapin_fpath(
                ["||".join(args)],
                df_questions_item,
                [MappingRule(expression= "src -> tgt as target,  target.name as name then SetOfficalGivenName{}(src, name)".format(rule_name))])
            ]
    elif mode == 'groups':
        rules = [
            wrapin_first_answers_rules(rule_name, args[0],df_questions_item,[MappingRule(expression = 'a.value as val -> tgt.family = val')]),
            wrapin_first_answers_rules(rule_name, args[1],df_questions_item,[MappingRule(expression = 'a.value as val -> tgt.given = val')]),
        ]
        if len(args) == 3:
            rules.append(wrapin_first_answers_rules(rule_name, args[2],df_questions_item,[MappingRule(expression = 'a.value as val -> tgt.given = val')]))
        
        return [MappingGroup(
            name = 'SetOfficalGivenName{}'.format(rule_name),
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                MappingRule(
                    expression = "src -> tgt.use = 'official'",
                    rules = rules
                )
            ]
        )]




####### MapValueSetExtCode :  to avoid concept maps when the system is predefined ###### 
#args[0]: valueset
#args[1]: path to map
#args[2] : coding /codeableConcept
def MapValueSetExtCode(mode, profile,question_id,df_questions, *args):
    rule_name = clean_group_name(question_id)
    tgttype = args[2] if len(args) == 3 else None
    if mode == 'rules':
        return [
            wrapin_fpath(
            [question_id],
            df_questions,
            [MappingRule(expression= "item.answer first as a then MapValueSetExtCode{}(a, tgt)".format(rule_name))])
        ]
    elif mode == 'groups':
        if len(args)< 2:
            print('Error SetOfficalGivenName must have 2 parameters, valueset name and mappath')
        # get Value set df
        maprules = get_valueset_map_source(args[0], args[1],tgttype)
        if maprules is not None:
            return [MappingGroup(
                name = 'MapValueSetExtCode{}'.format(rule_name),
                sources = [MappingGroupIO(name = 'src')],
                targets = [MappingGroupIO(name = 'tgt')],
                rules = [
                    MappingRule(
                        expression = "src -> tgt",
                        rules = [maprules]
                    )
                ]
            )]
# maptype :: system :: code 
def get_valueset_map_source(valueset_name, map_path, tgttype):
    sub_rules = []
    df = get_valueset_df(valueset_name, True)
    if df is not None:
        map_path_list =  get_map_path_list(map_path)
        for index, row in df.iterrows():
            if pd.notna(row['map'])  :
                map_concepts = row['map'].split('||')
                for mapping in map_concepts:
                    mapping_details = mapping.split('::')
                    if len(mapping_details)>1 or len(mapping_details)>0 and not mapping_details[0].lower().startswith('obs') :
                        to_code = mapping_details[len(mapping_details)-1]
                        if tgttype is not None and len(mapping_details)>1:
                            to_system = mapping_details[len(mapping_details)-2]
                            sub_rules.append(MappingRule(
                                expression = "src where value.code = '{0}'-> coding.code = '{1}',coding.system = '{2}' ".format(row['code'],to_code, to_system)
                            ))
                        else:
                            sub_rules.append(MappingRule(
                                expression = "src where value.code = '{0}' -> {1} = '{2}'".format(row['code'],map_path_list[len(map_path_list)-1] ,to_code)
                            ))
        
                        
        if tgttype is not None and tgttype.lower() == "coding":
            sub_rules = [MappingRule(
                expression = "{0}= create('Coding') as coding  ".format(map_path_list[len(map_path_list)-1],),
                rules = sub_rules
            )]
        elif  tgttype is not None and tgttype.lower() == "codeableconcept":
            sub_rules = [MappingRule(
                expression = "src -> {0}= create('CodeableConcept') as cc, cc.coding=create('Coding') as coding  ".format(map_path_list[len(map_path_list)-1]),
                rules = sub_rules
            )]

        return get_map_path_rule(map_path_list, sub_rules)
        



####### WalkMap :  to avoid concept maps when the system is predefined ###### 
#args[0]: path to map " assing ex " parent.childlvl1.childlvl2 = val
def MapWalk(mode, profile, question_id,df_questions,*args):
    # TODO support slicing and create
    val_a = "val" if  re.search(VAL_REGEX,args[0]) else "a"
    rule_name = clean_group_name(question_id)
    if mode == 'rules':
        rule = None
        if val_a == 'val':
            rule= MappingRule(expression= "a.value as val then MapWalk{1}(val, tgt)".format(rule_name))
        else:
            rule= MappingRule(expression= "a then MapWalk{1}(a, tgt)".format(rule_name))
        return [
            wrapin_first_answers_rules(
                rule_name,
                question_id,
                df_questions,
                [rule])
        ]
    elif mode == 'groups':
        if len(args)!= 1:
            print('Error MapWalk must have 1 parameters, valueset name and mappath')
        # get Value set df
        map_path_list =  get_map_path_list(args[0])
        
        rules = MappingRule(
            name = 'asgn',
            expression = map_path_list[-1]
            ) 
        map_path_list = map_path_list[:-1]
        return [MappingGroup(
                name = 'MapWalk{}'.format(rule_name),
                sources = [MappingGroupIO(name = 'src')],
                targets = [MappingGroupIO(name = 'tgt')],
                rules = [get_map_path_rule(map_path_list, rules, val_a)]
            )]

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
def SetCommunicationRequest(mode, profile, question_id,df_questions,*args):
    rule_name = clean_group_name(profile+question_id)
    id_prefix = clean_group_name(profile)
    if mode == 'rules':
        return None
    elif mode == 'groups':
        return [MappingGroup(
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
                
            ],  

        )]    


### create Classification
# args[x] post-coordination linkid under the item
def SetClassification(mode, profile, question_id,df_questions,*args):
    #FIXME
    rule_name = clean_group_name(profile+question_id)
    if mode == 'rules':
        return [
            wrapin_fpath(
            [question_id],
            df_questions,
            [MappingRule(expression="item  then {}(src,item, tgt)".format(rule_name))])
        ]
    elif mode == 'groups':
        
        # clinicalStatus active | recurrence | relapse | inactive | remission | resolved
        # subjet: Reference
        # encounter : Reference
        # verificationStatus
        # recordedDate: dateTime
        return [MappingGroup(
            name = rule_name,
            sources = [MappingGroupIO(name = 'src'),MappingGroupIO(name = 'item')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                        MappingRule(expression= "item.answer first as a",
                            rules = [
                            MappingRule(expression= "src.subject as sub -> tgt.subject = sub"),
                            MappingRule(expression= "src.encounter as en -> tgt.encounter = en"),
                            get_timestamp_rule(target = 'tgt.recordedDate' ),
                            MappingRule(expression= "src -> tgt.code = create('CodeableConcept') as cs",
                                rules = [MappingRule(expression= "src -> tgt.code = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= '{}', ccs.system = '{}'".format(question_id, get_custom_codesystem_url()))]),
                            MappingRule(expression= "a where value = true",
                                rules = [
                                    MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'active', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                                    MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'differential', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
                                ]
                            ),
                            MappingRule(expression= "a where value = false",
                                rules = [
                                    MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'inactive', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                                    MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'refuted', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
                                ])
                        ]),*get_post_coordination_rules(question_id,df_questions,*args)]),         
            ]

def get_post_coordination_rules(stem_code,df_questions, *args):
    rules = []

    for arg in args:
        rules.append(wrapin_fpath([arg],
            df_questions,
            [MappingRule(expression= "src -> tgt.extension  = create('Extension') as ext ,  ext.url ='{}/StructureDefinition/postcoordination',  ext.value =  create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= '{}', ccs.system = '{}'".format(get_fhir_cfg().canonicalBase,arg, get_custom_codesystem_url()))]
            )
        
        )
    return rules
### create Classification
# args[0] linkid for classificaitonchoice, valueSet

  
def SetClassificationFromChoice():
    pass