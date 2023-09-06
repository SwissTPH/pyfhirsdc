"""
 convert dataframe to to fhir coding system concept

"""
import logging

import pandas as pd
from fhir.resources.R4B.codesystem import CodeSystemConcept

from pyfhirsdc.config import (append_used_obs_valueset, append_used_valueset,
                              get_processor_cfg)
from pyfhirsdc.converters.utils import get_base_profile
from pyfhirsdc.converters.valueSetConverter import \
    get_value_set_additional_data_keyword

logger = logging.getLogger("default")


def generate_questionnaire_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions.dropna(axis=0, subset=['id']).dropna(axis=0, subset=['scope']).to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        if question['scope'] == get_processor_cfg().scope and 'initialExpression' in question and pd.isna(question['initialExpression']):
            concept.append(
                CodeSystemConcept(
                    definition = get_description(question),
                    code = question['id'],
                    display =  question["label"] if pd.notna(question["label"]) else None
                )
            )
    return concept

def get_description(question):
    return question["description"] if 'description' in question and pd.notna(question["description"]) else None

def generate_observation_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions[~df_questions['id'].isin(
        get_value_set_additional_data_keyword()
        )].dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        base_profile = get_base_profile(question['map_profile'])
        if base_profile == "Observation":
            concept.append(
                CodeSystemConcept(
                    definition =  get_description(question),
                    code = id,
                    display =  question["label"] if pd.notna(question["label"]) else None
                )
            )
    return concept

def generate_condition_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions[~df_questions['id'].isin(
        get_value_set_additional_data_keyword()
        )].dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        base_profile = get_base_profile(question['map_profile'])
        if base_profile == "Condition":
            concept.append(
                CodeSystemConcept(
                    definition =  get_description(question),
                    code = id,
                    display =  question["label"] if pd.notna(question["label"]) else None
                )
            )
    return concept

def generate_diagnosis_concept(df_questions):
    concept = []
    # remove the line without id
    questions = df_questions[~df_questions['id'].isin(
        get_value_set_additional_data_keyword()
        )].dropna(axis=0, subset=['id']).dropna(axis=0, subset=['map_profile']).set_index('id').to_dict('index')
    # remove the line without id
    for id, question in questions.items():
        base_profile = get_base_profile(question['map_profile'])
        if base_profile == "Diagnosis":
            concept.append(
                CodeSystemConcept(
                    definition =  get_description(question),
                    code = id,
                    display =   question["label"] if pd.notna(question["label"]) else None
                )
            )
    return concept

def generate_valueset_concept(df_value_set):
    concepts = []
    obs_concepts= []
    # remove the line without id
    value_set = df_value_set[~df_value_set['code'].isin(
        get_value_set_additional_data_keyword()
        )]
    len_origin = len(value_set)
    # Drop duplicate 
    value_set = value_set.drop_duplicates(subset='code', keep="last")
    len_cleanned = len(value_set)
    if len_origin !=len_cleanned:
        logger.warning("{} value were removed from the value set because other line have the same code".format(len_origin-len_cleanned))
    value_set = value_set.dropna(axis=0, subset=['code']).set_index('code').to_dict('index')
    # remove the line without id
    for code, question in value_set.items():
        concept = CodeSystemConcept(
                definition =get_description(question),
                code = code,
                display =  question["display"] if pd.notna(question["display"]) else None,
            )
        if "map" in  question and  pd.notna(question["map"]) and    question["map"].lower().startswith('obs'):
            obs_concepts.append(concept)
            append_used_obs_valueset(concept.code,concept.display)
        else:
            concepts.append(concept)
            append_used_valueset(concept.code,concept.display)
    return concepts, obs_concepts
