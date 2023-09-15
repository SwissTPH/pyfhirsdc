import json

from fhir.resources.R4B.activitydefinition import (ActivityDefinition,
                                               ActivityDefinitionDynamicValue)

from fhir.resources.R4B.expression import Expression
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.fhirtypes import Canonical

from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg
from pyfhirsdc.converters.utils import (adv_clean_name, clean_name,
                                        get_resource_url,get_pyfhirsdc_lib_name)
from pyfhirsdc.serializers.json import read_resource

from .extensionsConverter import append_unique



def create_activity_collect_with(questionnaire):
    #FIXME we should have {{context}} in questionnationnaire to define PATDOC or on the PD
    act_id = clean_name(questionnaire['id'])
    activity_definition = ActivityDefinition.parse_raw(json.dumps(get_defaut_fhir('ActivityDefinition-collect-with')))
    activity_definition.url=get_resource_url('ActivityDefinition',act_id) 
    activity_definition.kind = 'Task'
    activity_definition.id = act_id
    activity_definition.name = questionnaire['name']
    activity_definition.version=get_fhir_cfg().lib_version
    activity_definition.library = [Canonical(get_resource_url('Library', get_pyfhirsdc_lib_name(act_id),True))]
    #activity_definition.useContext = [
    #  UsageContext( 
    #    code = get_code(
    #      "http://terminology.hl7.org/CodeSystem/usage-context-type", 
    #      "task"),
    #    valueCodeableConcept = get_codableconcept_code(
    #      'http://terminology.hl7.org/CodeSystem/v3-ActCode', 
    #      'PATDOC',
    #      "Collect infornation with questionnaire {}".format(questionnaire['title'])))
    #]
    #activity_definition.code = get_codableconcept_code(
    #  "http://hl7.org/fhir/uv/cpg/CodeSystem/cpg-activity-type",
    #  "collect-information",
    #  "Collect information")
    # could nbe splitted into input.code / input.value
#{
#    "path" : "status",
#    "expression" : {
#      "language" : "text/fhirpath",
#      "expression" : "'draft' as String"
#    }
#  }
    
    new_ext = Extension(
        url = "http://hl7.org/fhir/uv/cpg/StructureDefinition/cpg-collectWith",
        valueCanonical = questionnaire['url'])
    if activity_definition.extension is None:
        activity_definition.extension = []
    append_unique(activity_definition.extension, new_ext, True)
    return activity_definition


def create_activity_propose_diagnosis(row,library):
    activity_definition = ActivityDefinition.parse_raw(json.dumps(get_defaut_fhir('ActivityDefinition-propose-diagnosis')))
    activity_definition.version=get_fhir_cfg().lib_version
    activity_definition.dynamicValue.append(
        ActivityDefinitionDynamicValue(
            path= "contained",
            expression= Expression(
            language = "text/cql-identifier",
            expression = f"generateCondition_{row['id']}")
        )
    )
    activity_definition.id= clean_name('propose-diagnosis-' + row['id'])
    activity_definition.url=get_resource_url('ActivityDefinition',activity_definition.id)
    activity_definition.library = [library.url+"|"+Canonical(library.version)]
    return activity_definition
