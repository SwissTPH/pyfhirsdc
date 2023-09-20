import logging
import os
import re

import pandas as pd
from pyfhirsdc.converters.mapHelpers.utils import get_timestamp_rule, wrapin_entry_create

from pyfhirsdc.config import get_defaut_path, get_fhir_cfg
from pyfhirsdc.converters.mapHelpers.utils import wrapin_fpath

from pyfhirsdc.converters.utils import (adv_clean_name, 
                                        get_custom_codesystem_url)
from pyfhirsdc.converters.valueSetConverter import (get_condition_valueset_df,
                                                    get_valueset_df)
from pyfhirsdc.models.mapping import ( MappingGroup, MappingGroupIO,
                                       MappingRule)


logger = logging.getLogger("default")
### create Classification
# args[x] post-coordination linkid under the item
def SetCondition(mode, profile, question_id,df_questions,*args):
    #FIXME
    rule_name = adv_clean_name(profile+question_id)
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
        return [set_generic_condition(rule_name,question_id,[],get_condition_conf_status_rules() + get_post_coordination_rules(question_id,df_questions,*args))]
    elif mode == 'docs':    
        return get_condtion_docs(profile,question_id,df_questions, len(args) )
    
def get_condtion_docs(profile,question_id,df_questions, nb_postcoordination= 0):
        
        return   {
            'type' : profile,
            'code' : question_id,
            'valueType' : 'boolean',
            'description': 'generate a condition with possible postcoordition' if nb_postcoordination > 0 else 'generate a condition'
        }

def get_condition_conf_status_rules():
    return [
        MappingRule(expression= "item.answer first as a where value.code = 'agree' or value = true",
            rules = [
                MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'active', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'confirmed', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
            ]
        ),
        MappingRule(expression= "item.answer first as a where value.code = 'disagree' or value = false",
            rules = [
                MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'inactive', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'refuted', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
            ])
    ]


### create Classification
# args[x] post-coordination linkid under the item
def SetConditionYesNo(mode, profile, question_id,df_questions,*args):
    #FIXME
    rule_name = adv_clean_name(profile+question_id)
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
        return [set_generic_condition(rule_name,question_id, get_post_coordination_rules(question_id,df_questions,*args))]
    elif mode == 'docs':    
        return get_condtion_docs(profile,question_id,df_questions, len(args) )
    
def get_post_coordination_rules(stem_code,df_questions, *args):
    rules = []

    for arg in args:
        if arg == '':
            logger.error("arg cannot be empty for %s",stem_code)
        
        rules.append(wrapin_fpath([arg],
            df_questions,
            [
                MappingRule(expression= "item.answer first as a where a.value=true",
                    rules = [
                        MappingRule(
                            expression= "src -> tgt.extension  = create('Extension') as ext ,  ext.url ='{}/StructureDefinition/postcoordination',  ext.value =  create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= '{}', ccs.system = '{}'".format(get_fhir_cfg().canonicalBase,arg, get_custom_codesystem_url()))
                        ]
                )
            ]
            )            
        )
    return rules
### create Classification
# args[0] linkid for classificaitonchoice, valueSet
def set_generic_condition(name, code, status_rules, other_rules = []):
    return MappingGroup(
        name = name,
        sources = [MappingGroupIO(name = 'src'),MappingGroupIO(name = 'item')],
        targets = [MappingGroupIO(name = 'tgt')],
        rules = [
                MappingRule(expression= "item.answer first as a",
                    rules = [
                    MappingRule(expression= "src.subject as sub -> tgt.subject = sub"),
                    MappingRule(expression= "src.encounter as en -> tgt.encounter = en"),
                    get_timestamp_rule(target = 'tgt.recordedDate' ),
                    MappingRule(expression= "src -> tgt.code = create('CodeableConcept') as cs",
                        rules = [MappingRule(expression= "src -> tgt.code = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= '{}', ccs.system = '{}'".format(code, get_custom_codesystem_url()))]),
                    *status_rules
                ]),*other_rules]
    )       
            
def get_classification_conf_status_rules():
    return [
        MappingRule(expression= "a where value = true",
            rules = [
                MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'active', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'confirmed', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
            ]
        ),
        MappingRule(expression= "a where value = false",
            rules = [
                MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'inactive', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
                MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'refuted', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
            ])
    ]
    
def get_add_classification_status_rules():
    return [
        MappingRule(expression = " a -> tgt.clinicalStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'active', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-clinical'"),
        MappingRule(expression = " a -> tgt.verificationStatus = create('CodeableConcept') as cs, cs.coding = create('Coding') as ccs, ccs.code= 'unconfirmed', ccs.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'")
    ]

def SetConditionMultiple(mode, profile, question_id, df_questions, *args):

    question = df_questions[df_questions.id == question_id].iloc[0]
    if 'select_condition' in question.type :
        df_valueset = get_condition_valueset_df(df_questions)
    else:
        if len(args)!= 1:
            logger.error('SetConditionMultiple must have 1 parameters')
            return None
        df_valueset = get_valueset_df(args[0], True) 
     
    if mode == 'rules':
        return get_base_cond_muli_rules(profile, question_id,df_questions,df_valueset)
    elif mode == 'groups':
        return get_base_cond_muli_groups(profile,question_id,df_valueset)
    elif mode == 'docs':    
        return None
        

def get_base_cond_muli_rules(profile, question_id,df_questions,df_valueset):
    rules = []
 
    
    #src where src.item.where(linkId='EmCare.A.DE16').answer.exists(value.code = 'EmCare.A.DE17')=false -> tgt.gender = 'male' 'emcareade17';
    for index, row in df_valueset.iterrows():
        rule_name = adv_clean_name(profile + question_id + row['code']) 
        code=row['code']
        rules.append(MappingRule(
            expression = "src where src.item.where(linkId='{0}').answer.where(value.code = '{1}') ".format(question_id, code),
            rules = [wrapin_entry_create( profile, question_id,df_questions,[MappingRule(expression = 'src then {}(src,item,tgt)'.format(rule_name) )])]
        ))

            
    return  rules


def get_base_cond_muli_groups(profile, question_id,df):
    groups = []
    for index, row in df.iterrows():
        rule_name = adv_clean_name(profile + question_id + row['code']) 
        groups.append(set_generic_condition(rule_name,row['code'],get_add_classification_status_rules()))
    return groups
