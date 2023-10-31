import logging
import os

import pandas as pd

from pyfhirsdc.converters.utils import (get_custom_codesystem_url, get_fpath,
                                        get_resource_url, inject_variables, get_base_profile)
from pyfhirsdc.converters.valueSetConverter import get_valueset_df
from pyfhirsdc.models.mapping import MappingRule

logger = logging.getLogger("default")

import pkgutil


def get_custom_helpers():
    custFunc = {}
    root = __file__
    path = os.path.join(os.path.dirname(__file__),'custom')
    for loader, module_name, is_pkg in pkgutil.walk_packages([path]):
        _module = loader.find_module(module_name).load_module(module_name)
        for name, val in _module.__dict__.items(): # iterate through every module's attributes
            if callable(val)and  (not str(name).startswith("_")) and (name not in custFunc):
                custFunc[name]=val
    return custFunc



        

FHIR_ONELINER_PROFILES = [
    "Condition",
    "Observation",
    "CommunicationRequest",
]

VAL_REGEX = "[ =]*val(?:[^\w]|$)"

def wrapin_entry_create(profile,question_id,df_questions_item, rules, condition = ''):
    base_profile = get_base_profile(profile)
    return wrapin_fpath(["{0}".format(question_id)],df_questions_item,[
                    MappingRule(expression = f"src{condition} -> bundle.entry as entry ",
                    rules = [
                        MappingRule(expression = "src -> entry.request as request, request.method = 'POST' , uuid() as uuid, request.url = append('/{}/', uuid)".format(base_profile)),
                        MappingRule(
                            expression = "src -> entry.resource = create('{0}') as tgt".format(base_profile),
                            rules = rules
                )])])
    
    
def wrapin_fpath(fpaths,df_questions,rules):
    a_ids = fpaths.pop(0).split('||')
    linkid=a_ids[0]
    # if on the leaf there is several id, only the parent of the first will be taken
    fpaths = get_fpath(df_questions,linkid, fpaths)
    leaf_rule = None
    fpaths_len = len(fpaths)
    if fpaths_len==1:
        return MappingRule(
            expression = "src.item first as item  where linkId = '{}' and answer.exists()".format("' or linkId= '".join(a_ids)),
            rules = rules
        )
    else:
        # we trust the content of a_ids and remove the result from get_fpath
        fpaths.pop(0)
        leaf_rule = MappingRule(
            expression = "itm{}.item first as item  where linkId =  '{}' and answer.exists()".format(len(fpaths),"' or linkId= '".join(a_ids)),
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

def is_oneliner_profile(profile):
    base_profile = get_base_profile(profile)
    if base_profile in FHIR_ONELINER_PROFILES:
        return True





def get_questions_profiles(df_questions):
    profiles = df_questions['map_profile'].dropna().unique()
    return profiles

def get_profiles_questions(df_questions, profile):
    return df_questions[df_questions['map_profile'] == profile ].to_dict('index')

def get_helper(question):
    helper_func = None
    helper_args = []
    if 'map_resource' in question and pd.notna(question['map_resource']):
        import pyfhirsdc.converters.mapHelpers.custom 
        helper_array = str(question['map_resource']).split('::')
        helper_func = helper_array[0].strip()
        # quite if not helper is found
        if " " in helper_func.strip():
            return None, None
        #elif helper_func not in globals():
        #    logger.error("Mapping function {} not found".format(helper_func))
        #    return None, None
        if len(helper_array)>1:
            helper_args = [x.strip() for x in helper_array[1].split('||')] if len(helper_array)>1 else []
    return helper_func, helper_args

    



def generate_helper(helper_func, mode, profile, question_id,df_questions, *helper_args):
    
    return  get_custom_helpers()[helper_func](mode,profile , question_id,df_questions, *helper_args )        

def wrapin_first_answers_rules(rule_name, question_id,df_questions_item, rules):
    return wrapin_fpath([question_id],df_questions_item,[MappingRule(
            expression = "item.answer first as a",
            rules = rules
        )]
    )
    
     
def get_val_rule(rule_name, expression):
    return MappingRule(
        expression  = "item.answer first as a",
        name = 'a'+rule_name,
        rules = [ MappingRule( 
            expression  = "a.value as val -> {0}".format(inject_variables(expression)),
            name = 'a'+rule_name
        )]
    )
def get_ans_rule(rule_name, expression):
    return MappingRule( 
            expression  = "item.answer first as a -> {0}".format(inject_variables(expression)),
            name = 'a'+rule_name
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
    
def get_timestamp_rule( target = 'tgt.issued' ):
    return MappingRule(    
                        expression = "src.item as itemtimestamp where linkId  =  'timestamp'",
                        rules = [
                            MappingRule(expression = 'itemtimestamp.answer first as atimestamp',
                                rules = [MappingRule(expression = 'atimestamp.value as val -> {} = val '.format(target))])]
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

