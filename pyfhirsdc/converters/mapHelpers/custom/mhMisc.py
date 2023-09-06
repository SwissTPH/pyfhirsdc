import logging
import os
import re

import pandas as pd
from pyfhirsdc.converters.mapHelpers.utils import VAL_REGEX,  wrapin_first_answers_rules, wrapin_fpath

from pyfhirsdc.converters.utils import (adv_clean_name )
from pyfhirsdc.converters.valueSetConverter import (get_valueset_df)
from pyfhirsdc.models.mapping import ( MappingGroup, MappingGroupIO,
                                       MappingRule)


logger = logging.getLogger("default")

####### SetOfficalGivenNameSetOfficalGivenName :  to have all the name under a single "official" ###### 
#args[0]: question name last
#args[1]: question name first
#args[2]: question name mid
def SetOfficalGivenName(mode, profile, question_id,df_questions_item, *args):
    rule_name = adv_clean_name(profile)
    if len(args)< 2:
        logger.error('SetOfficalGivenName must have 2 or 3 parameters')
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
    elif mode == 'docs':    
            return   {
            'type' : profile,
            'code' : 'name',
            'valueType' : 'HumanName',
            'description': 'set a ressource value'
        }



####### MapValueSetExtCode :  to avoid concept maps when the system is predefined ###### 
#args[0]: valueset
#args[1]: path to map
def MapValueSetExtCode(mode, profile,question_id,df_questions, *args):
    rule_name = adv_clean_name(question_id)
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
            logger.error('SetOfficalGivenName must have 2 parameters, valueset name and mappath')
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
        elif mode == 'docs':    
            return   {
            'type' : profile,
            'code' : args[1],
            'valueType' : 'CodeableConcept',
            'description': 'set human name'
        }
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
    rule_name = adv_clean_name(question_id)
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
            logger.error('MapWalk must have 1 parameters, valueset name and mappath')
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
    elif mode == 'docs':    
            return   {
            'type' : profile,
            'code' : args[0],
            'valueType' : df_questions[df_questions.id==question_id]['type'],
            'description': 'set a ressource value'
        }

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
