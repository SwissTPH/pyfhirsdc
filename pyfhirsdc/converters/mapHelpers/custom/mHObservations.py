import logging
import os
import re

import pandas as pd


from pyfhirsdc.converters.mapHelpers.utils import get_obs_meta_rule, get_rand_identifier_rule, get_timestamp_rule, wrapin_entry_create, wrapin_first_answers_rules
from pyfhirsdc.converters.utils import (clean_group_name, 
                                        get_custom_codesystem_url)
from pyfhirsdc.converters.valueSetConverter import (get_valueset_df)
from pyfhirsdc.models.mapping import ( MappingGroup, MappingGroupIO,
                                       MappingRule)

logger = logging.getLogger("default")
def SetObservationValueSetStr(mode, profile, question_id, df_questions, *args):
    #row = df_questions[df_questions.id == question_id].head(1)
    rule_name = clean_group_name(profile + question_id ) 
    if len(args)!= 1:
        logger.error('SetObservation must have 1 parameters')
        return None
    
    if mode == 'groups':
        df_valueset = get_valueset_df(args[0], True) 
        return [set_generic_observation_v2( profile, rule_name, question_id, [wrapin_first_answers_rules(rule_name, question_id, df_questions, get_obs_valueset_str_rules(df_valueset))])]
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'CodeableConcept', df_questions)
    
    
def get_obs_valueset_str_rules(df_valueset):
    rules_main = []
    for index, concept in df_valueset.iterrows():
        rules_main.append(
            MappingRule(
            expression = "a where value = '{}', a.value as val".format(concept['display']),
            rules = [ MappingRule(
                expression="val -> tgt.value = create('CodeableConcept') as cc, cc.coding = create('Coding') as c, c.code={}, c.system= '{}', tgt.status = 'final'".format(concept['code'], get_custom_codesystem_url())
            )])
        )
        
    return rules_main


def get_generic_obs_cancelled_group():
    pass
def SetObservationCodeStr(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code, get_obs_code_str_rules(code,df_questions_item))]
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'CodeableConcept', df_questions_item)
    
    
def get_obs_code_str_rules(question_id, df_questions_item):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a.value as val",
    rules = [ MappingRule(
        expression="val -> tgt.value = create('CodeableConcept') as cc, cc.coding = create('Coding') as c, c.code=val, c.system= '{}', tgt.status = 'final'".format( get_custom_codesystem_url())
    )])])]

 ####### SetObservation :  set the value of an observation, obs will never be cancelled  ###### 
 #args[0]: question name
 #args[1]: none name
 # 
def SetObservationCode(mode, profile, question_id,df_questions_item, *args):
    if mode == 'groups':
        none_name = args[0] if len(args)>1 else 'none'
        code =  question_id
        rule_name = clean_group_name(question_id)
        return [set_generic_observation_v2( profile, rule_name, code, get_obs_value_rules(code,df_questions_item, none_name))]
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'CodeableConcept', df_questions_item)
    
def get_obs_value_rules(question_id, df_questions_item,none_name):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a.value as val",
    rules = [MappingRule(
        expression = "val where val.code = '{}' -> tgt.status = 'cancelled'".format(none_name),
    ), MappingRule(
        expression="val where val.code != '{}' -> tgt.value = create('CodeableConcept') as cc, cc.coding = val, tgt.status = 'final'".format(none_name)
    )])])]
            
    




def SetObservation(mode,  profile, question_id,df_questions_item, *args):
    return SetObservationQuantity(mode,  profile, question_id,df_questions_item, *args)   
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
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'Quantity', df_questions_item)
    
    
def get_base_obs_docs(question_id, valueType, df_questions_item):
    return   {
            'type' : 'Observation',
            'code' : question_id,
            'valueType' : valueType,
            'description': df_questions_item[df_questions_item.id==question_id].iloc[0]['label']
            
        }

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
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'boolean', df_questions_item)
    
    
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
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'boolean', df_questions_item)
    
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
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'boolean', df_questions_item)
    
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
    elif mode == 'docs':
        return get_base_obs_docs(question_id, 'boolean', df_questions_item)
    
def get_obs_bool_code_rules(question_id, df_questions_item):
    rule_name = clean_group_name(question_id)
    return [ wrapin_first_answers_rules(rule_name, question_id, df_questions_item,[MappingRule(
        expression = "a.value as val",
    rules = [MappingRule(
        expression = "val where val.code = 'true' -> tgt.status = 'final',tgt.value = true ",
    )])])]
            

 ####### SetObservationMultiple :  works only with valueset, will generate an obs for all, cancelled is not selected but for the one with value none   ###### 
# args[0] : valueSet name
def SetObservationMultiple(mode, profile, question_id, df_questions, *args):
    if len(args)!= 1:
        logger.error('SetObservation must have 1 parameters')
        return None
    df_valueset = get_valueset_df(args[0], True)   
    if mode == 'rules':
        return get_base_obs_muli_rules(profile, question_id,df_questions,df_valueset)
    elif mode == 'groups':
        return get_base_obs_muli_groups(profile, question_id,df_valueset)
    elif mode == 'docs':
        return get_docs_obs_muli(question_id,df_valueset,  df_questions)
    

def get_docs_obs_muli(question_id,df_valueset, df_questions_item):
    docs = []
    for index, row in df_valueset.iterrows():
        if "map" in row and   pd.notna(row["map"]) and row['map'].lower().startswith('obs'):
            docs.append(
                {
                    'type' : 'Observation',
                    'code' : question_id+ "&" +  row['code'],
                    'valueType' : 'boolean',
                    'description': '{}:{}'.format(
                        df_questions_item[df_questions_item.id==question_id].iloc[0]['label'],
                        row['display']
                    )
                }
            )
  
    return docs         
    
        

def get_base_obs_muli_rules(profile, question_id,df_questions,df_valueset):
    rules = []
 
    
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