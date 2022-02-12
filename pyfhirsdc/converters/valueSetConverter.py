from fhir.resources.fhirtypes import Canonical, Code, Uri, DateTime
from fhir.resources.valueset import ValueSet, ValueSetCompose,\
     ValueSetComposeInclude, ValueSetComposeIncludeConcept,\
     ValueSetComposeIncludeConceptDesignation

from pyfhirsdc.utils import get_custom_codesystem_url


def get_value_set_compose(compose, name, df_value_set):
    df_value_set = df_value_set[~df_value_set.index.isin(
        get_value_set_additional_data_keyword()
    )].to_dict('index')
    if compose is None:
        compose = ValueSetCompose.construct()
    if compose.include is None or len(compose.include)==0:
        include = ValueSetComposeInclude.construct()
    else:
        # we assume there is only one include
        include = compose.include.pop()
    if include.system is None:
        include.system = Uri( get_custom_codesystem_url())

    if include.concept is None:
        concepts = []
    else:
        concepts =include.concept

    for id, line in df_value_set.items():
        if line['label'] is not None and\
            [c for c in concepts if c.code == id] == []:
                concept = ValueSetComposeIncludeConcept(
                    code = Code(id),
                    display = line['label'],
                )
                if line['description'] is not None:
                    concept.designation = [ValueSetComposeIncludeConceptDesignation(
                        value = line['description']
                    )]
                concepts.append(concept)
    include.concept = concepts

    compose.include = [include]
    return compose


def get_value_set_additional_data(vs, df_value_set):
    # need to support {{title}}
    df_value_set = df_value_set[df_value_set.index.isin(
        get_value_set_additional_data_keyword()
        )].to_dict('index')
    for id, line in df_value_set.items():
        if id == '{{title}}':
            if  line['label']!='na':
                vs.title = line['label']
            if line['description']!='na':
                vs.description = line['description']

    return vs


def get_value_set_additional_data_keyword():
    return ['{{title}}']