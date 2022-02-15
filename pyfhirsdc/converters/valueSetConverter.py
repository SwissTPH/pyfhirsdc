from fhir.resources.fhirtypes import  Code, Uri
from fhir.resources.valueset import  ValueSetCompose,\
     ValueSetComposeInclude, ValueSetComposeIncludeConcept,\
     ValueSetComposeIncludeConceptDesignation
import numpy

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
        # TODO use scope to have more incldues
        include = compose.include.pop()
    if include.system is None:
        include.system = Uri( get_custom_codesystem_url())

    if include.concept is None:
        concepts = []
    else:
        concepts =include.concept

    for id, line in df_value_set.items():
        concepts = get_value_set_conept(concepts, id, line)
    include.concept = concepts

    compose.include = [include]
    return compose

def get_value_set_conept(concepts, id, line):
    if line['display'] is not None and\
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
    df_value_set = df_value_set[df_value_set.index.isin(
        get_value_set_additional_data_keyword()
        )].to_dict('index')
    for code, line in df_value_set.items():
        if code == '{{title}}':
            vs = get_value_set_title(vs, line)
        elif code == '{{exclude}}':
            vs.exclude = get_value_set_exclude(vs.exclude, line)
    return vs


def get_value_set_exclude(exclude, line):
    if line['display'] is not None and line['display'] is not numpy.na:
        exclude_line = ValueSetComposeInclude(
            system = Uri(line['display'])
        )
        found = False
        for ex in exclude:
            if ex.system == line['display']:
                found = True
        if not found:
            exclude.append(exclude_line)
    return exclude

def get_value_set_title(vs, line):
    if  line['display'] is not numpy.nan:
        vs.title = line['display']
    if line['definition'] is not numpy.na:
        vs.definition = line['definition']
    return vs


def get_value_set_additional_data_keyword():
    return [
        '{{title}}',
        '{{exclude}}',
        '{{choiceColumn}}',
        '{{url}}'
         ]