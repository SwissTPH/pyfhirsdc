import pandas as pd
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.fhirtypes import Code, Uri
from fhir.resources.R4B.questionnaire import QuestionnaireItemAnswerOption
from fhir.resources.R4B.valueset import (ValueSetCompose, ValueSetComposeInclude,
                                     ValueSetComposeIncludeConcept,
                                     ValueSetComposeIncludeConceptDesignation)

from pyfhirsdc.config import get_dict_df, get_processor_cfg, set_dict_df
from pyfhirsdc.converters.extensionsConverter import get_item_media_ext
from pyfhirsdc.converters.utils import get_custom_codesystem_url, get_media, METADATA_CODES


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



def get_condition_valueset_df(df_questions):
    df_classification = df_questions.dropna(axis=0,subset = ['map_profile'])
    df_classification = df_classification[df_classification.map_profile.str.contains("Condition") & (df_classification['type']!= 'select_condition') ]
    if len(df_classification)>0:
        df_classification.rename(columns = {'id':'code', 'display':'display_conf', 'label':'display', 'description':'definition'}, inplace = True)
        return df_classification      

def get_value_set_answer_options(df_value_set):
    
    options = []
    for index, line in df_value_set.iterrows():
        options.append(
            QuestionnaireItemAnswerOption(
                valueCoding = Coding(
                    code = line['code'], 
                    display = line['display'],
                    system=get_custom_codesystem_url()
                ),
                extension = get_value_set_extensions(line)
            )
        )
    if len(options)>0:
        return options
    

def  get_value_set_extensions(line):
    extensions = []
    media_type, media_url = get_media(line)
    if media_type is not None:
        extensions.append(get_item_media_ext(media_type, media_url, True))
    if len(extensions)>0:
        return extensions


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
    value_set_dict = df_value_set.to_dict('index')
    for id, line in value_set_dict.items():
        concepts = get_value_set_concept(concepts, line['code'], line)
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
        if 'definition' in line and line['definition'] is not None and pd.notna(line['definition']):
            concept.designation = [ValueSetComposeIncludeConceptDesignation(
                value = line['definition']
            )]
        if concept not in concepts:
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
            line = pd.Series([{'scope': value_set_filter, }])
            df_value_set_in = pd.concat([df_value_set_in, line], ignore_index=True)
            #df_value_set_in = df_value_set_in.append(line, ignore_index = True)

    df_value_set = df_value_set_in[df_value_set_in['scope'].isin(value_set_filters)]
    return get_value_set_in_ex_cludes(excludes, df_value_set)
    

def get_value_set_title(vs, line):
    if  pd.notna(line['display']):
        vs.title = line['display']
    if pd.notna(line['definition']):
        vs.description = line['definition']
    return vs

#TODO: check if it makes sense to have the valuset special id mixed with questionnaire/libs ones


def get_value_set_additional_data_keyword():
    return METADATA_CODES

   
def get_valueset_df(valueset_name, filtered = False):
    dict_df = get_dict_df()
    if "valueset" in dict_df:
        df_valueset = dict_df['valueset']
        if filtered :
            df_valueset = df_valueset[~ df_valueset.code.isin(METADATA_CODES)] 
        return df_valueset[df_valueset.valueSet == valueset_name]
    
# scope	valueSet	code	display	definition


def add_concept_in_valueset_df(list_name ,concepts):
    values = []
    dict_df = get_dict_df()
    if "valueset" in dict_df:
        df_valueset = dict_df['valueset']  
        for concept in concepts:
            if len(df_valueset[(df_valueset.code == concept.code) & (df_valueset.valueSet == list_name)]) == 0:             
                values.append({
                    'scope':get_processor_cfg().scope,
                    'valueSet':list_name,
                    'code': concept.code ,
                    'display': concept.display,
                    'definition': concept.definition
                })
            # ADD VALUE TO DF
        df_dictionary = pd.DataFrame(values)
        df_valueset = pd.concat([df_valueset, df_dictionary], ignore_index=True)
        dict_df['valueset'] =  df_valueset
        set_dict_df(dict_df)  
