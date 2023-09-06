import logging
import os
import re

import pandas as pd

from pyfhirsdc.config import get_defaut_path, get_processor_cfg
from pyfhirsdc.converters.extensionsConverter import \
    get_structure_map_extension
from pyfhirsdc.converters.mapHelpers.utils import (VAL_REGEX, generate_helper,
                                                   get_ans_rule,
                                                   get_helper,
                                                   get_profiles_questions,
                                                   get_questions_profiles,
                                                   get_val_rule,
                                                   is_oneliner_profile,
                                                   wrapin_entry_create,
                                                   wrapin_first_answers_rules,
                                                   wrapin_fpath)
from pyfhirsdc.converters.utils import (adv_clean_name, clean_name,
                                        get_resource_url, get_base_profile)
from pyfhirsdc.models.mapping import (Mapping, MappingGroup, MappingGroupIO,
                                      MappingIO, MappingRule)
from pyfhirsdc.serializers.mappingSerializer import write_mapping_file
from pyfhirsdc.serializers.utils import get_resource_path, write_resource

logger = logging.getLogger("default")



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
            url = get_resource_url('StructureDefinition',adv_clean_name(profile)),
            alias = profile
        ))
    # create the SM ressource from HAPI server response
    if mapping.groups and len(mapping.groups)>0:
        structure_map = write_mapping_file(map_filepath, mapping)
        if structure_map is not None:
            write_resource(filepath, structure_map, get_processor_cfg().encoding)
    else:
        logger.warning("No mapping found for the questionnaire {0}".format(questionnaire_name))

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
            questions =  get_profiles_questions(df_questions_item, profile)
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
def get_outputs_docs( df_questions_item):
    docs = []
    questions = df_questions_item.to_dict('index')
    for question in questions.values():
        doc=None
        helper_func, helper_args= get_helper(question)
        if pd.notna(question['map_profile']) and question['map_profile'] != '':
            profile = get_base_profile(question['map_profile'])
            # get main rules from helper
            if helper_func is not None:
                doc = generate_helper(helper_func, 'docs', profile, question['id'],df_questions_item, *helper_args)
            if doc is not None:
                if isinstance(doc, list):
                    docs+=doc
                else:
                    docs.append(doc)
    return docs       
        

# this function create as many ressource as get_helper 'rules' function returns rules
def get_post_oneliner_bundle_profile_rule(profile,question,df_questions_item):
    
    rule_name = adv_clean_name(profile+question['id'])

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




def get_post_bundle_profile_rule(profile,df_questions_item):
    rule_name = adv_clean_name(profile)
    base_profile = get_base_profile(profile)
    logger.debug("create mapping rule, expect to find %sid",rule_name)
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



def get_put_bundle_profile_rule(profile,df_questions_item):
    rule_name = adv_clean_name(profile)
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
            name = adv_clean_name(profile),
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
    questions =  get_profiles_questions(df_questions_item, profile)
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



def get_mapping_detail(question_name, question, df_questions_item):
    #TODO manage transform evaluate/create
    # item that have childen item are created then the children rule will create the children Items
    # example rule 13 and 14 http://build.fhir.org/ig/HL7/sdc/StructureMap-SDOHCC-StructureMapHungerVitalSign.json.html
    #profileType, element, valiable = explode_map_resource(question['map_resource'])
    rules = None
    groups = None
    #logger.info("Mapping ``{0}`` added".format(fhirmapping))wrapin_entry_create(profile,question,df_questions_item, rules)
    if  'map_resource' in question\
        and pd.notna(question['map_resource'])\
        and question['map_resource'] is not None:
        
        helper_func ,helper_args = get_helper(question)
        if helper_func is not None:
            rules = generate_helper(helper_func, 'rules', question['map_profile'], question_name, df_questions_item ,*helper_args)
            groups  =  generate_helper(helper_func, 'groups', question['map_profile'], question_name,df_questions_item, *helper_args)

        else:
            rule_name = adv_clean_name(question_name)
            if question['map_resource'].strip()[-1:] == ";":
                logger.warning("the map ressource must not end with ;")

            # if variable on root, element is the resource itself
            match =  re.search(VAL_REGEX,question['map_resource'])
            rules = [
                wrapin_fpath([question_name],
                    df_questions_item,
                    [ get_val_rule(rule_name, question['map_resource']) if match else get_ans_rule(rule_name, question['map_resource'])]
                )
            ]

    return rules, groups




##### helpers 



        

##### mapping snippet


            


def add_mapping_url(resource, mapping):
    resource.extension = get_structure_map_extension(
            resource.extension, 
            mapping.url
            )
    return resource


def get_ref_groups(profile):
    base_profile = get_base_profile(profile)
    rule_name= adv_clean_name(profile)
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

 



def get_structuremap_outputs(df_questionnaire):
  # check if there is Patient, Encounter, Task, Observation, Condition
  # in case helpers retrive the details
  
  
  pass


