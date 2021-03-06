from fhir.resources.fhirtypes import  Code, Uri
from fhir.resources.valueset import  ValueSetCompose,\
     ValueSetComposeInclude, ValueSetComposeIncludeConcept,\
     ValueSetComposeIncludeConceptDesignation
import numpy
import pandas as pd
from pyfhirsdc.config import get_processor_cfg

from pyfhirsdc.converters.utils import get_custom_codesystem_url


def get_value_set_compose(compose, name, df_value_set_in):

    if compose is None:
        compose = ValueSetCompose.construct()
    if not hasattr(compose, 'exclude') or compose.exclude is None:
        compose.exclude = []
    compose.exclude = get_value_set_excludes(compose.exclude, name, df_value_set_in )
    if not hasattr(compose, 'include') or compose.include is None:
        compose.include = []
    compose.include = get_value_set_includes(compose.include, name, df_value_set_in )
    return compose

def get_value_set_includes(includes, name, df_value_set_in):
    # add the include of  concept from other codesystems
    value_set_filters = df_value_set_in[
        (df_value_set_in['code'] == '{{include}}') 
        & (df_value_set_in['valueSet']== name)
        ]['display'].unique()
    
    for value_set_filter in value_set_filters:
        # add a line for the system fully excluded
        if len(df_value_set_in[df_value_set_in['valueSet'] == value_set_filter]['code'])==0:
            line = {'scope': value_set_filter, } 
            df_value_set_in = df_value_set_in.append(line, ignore_index = True)
    df_value_set = df_value_set_in[~df_value_set_in['code'].isin(
        get_value_set_additional_data_keyword()
    )]
    df_value_set = df_value_set[df_value_set['valueSet']== name]
    return get_value_set_in_ex_cludes(includes, df_value_set)

def get_value_set_in_ex_cludes(includes, df_value_set):
    includes_out = []
    systems = df_value_set['scope'].unique()
    for system in systems:
        if system == get_processor_cfg().scope:
            system = get_custom_codesystem_url()
        includes_in = [inc for inc in includes if inc.system == system]
        if len(includes_in)>0:
            include = get_value_set_in_exclude(system, includes_in[0], df_value_set)
        else:
            include = get_value_set_in_exclude(system, None, df_value_set)
        if include is not None:
            includes_out.append(include)
    # add the includes defined manally
    if includes is not None:
        for incl in includes:
            if len([inc for inc in includes if inc.system == incl.system]) == 0:
                includes_out.append(incl)
    return includes_out

def get_value_set_in_exclude(system, include, df_value_set):

    if include is None:
        include = ValueSetComposeInclude.construct()
    if include.system is None:
        include.system = Uri(system)

    if include.concept is None:
        concepts = []
    else:
        concepts = include.concept
    value_set_dict = df_value_set.set_index('code').to_dict('index')
    for id, line in value_set_dict.items():
        concepts = get_value_set_concept(concepts, id, line)
    include.concept = concepts

    return include


def get_value_set_concept(concepts, id, line):
    if line['display'] is not None and\
         pd.notna(line['display']) and\
            [c for c in concepts if c.code == id] == []:
        concept = ValueSetComposeIncludeConcept(
            code = Code(id),
            display = line['display'],
        )
        if line['definition'] is not None:
            concept.designation = [ValueSetComposeIncludeConceptDesignation(
                value = line['definition']
            )]
        concepts.append(concept)
    return concepts



def get_value_set_additional_data(vs, df_value_set):
    # need to support {{title}}
    #df_value_set = df_value_set[df_value_set.index.isin(
    #    get_value_set_additional_data_keyword()
    #    )].to_dict('index')
    for index, line in df_value_set.iterrows():
        if line['code'] == '{{title}}':
            vs = get_value_set_title(vs, line)
    return vs



def get_value_set_excludes(excludes, name, df_value_set_in):
    value_set_filters = df_value_set_in[
        (df_value_set_in['code'] == '{{exclude}}') 
        & (df_value_set_in['valueSet']== name)
        ]['display'].unique()
    
    for value_set_filter in value_set_filters:
        # add a line for the system fully excluded
        if len(df_value_set_in[df_value_set_in['valueSet'] == value_set_filter]['code'])==0:
            line = {'scope': value_set_filter, } 
            df_value_set_in = df_value_set_in.append(line, ignore_index = True)

    df_value_set = df_value_set_in[df_value_set_in['scope'].isin(value_set_filters)]
    return get_value_set_in_ex_cludes(excludes, df_value_set)
    

def get_value_set_title(vs, line):
    if  pd.notna(line['display']):
        vs.title = line['display']
    if pd.notna(line['definition']):
        vs.description = line['definition']
    return vs


def get_value_set_additional_data_keyword():
    return [
        '{{title}}',
        '{{exclude}}',
        '{{include}}',
        '{{choiceColumn}}',
        '{{url}}'
         ]