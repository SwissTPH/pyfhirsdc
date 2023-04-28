import json

from fhir.resources.activitydefinition import (ActivityDefinition,
                                               ActivityDefinitionDynamicValue)
from fhir.resources.expression import Expression
from fhir.resources.extension import Extension
from fhir.resources.fhirtypes import Canonical

from pyfhirsdc.config import get_defaut_fhir, get_fhir_cfg
from pyfhirsdc.converters.utils import (clean_group_name, clean_name,
                                        get_resource_url)
from pyfhirsdc.serializers.json import read_resource

from .extensionsConverter import append_unique


def init_activity(filepath, id):
    #activity_json = read_resource(filepath, "ActivityDefinition")
    default =get_defaut_fhir('ActivityDefinition')
    #if activity_json is not None :
     #   activity = ActivityDefinition.parse_raw( json.dumps(activity_json))  
    #elif default is not None:
        # create file from default
    activity = ActivityDefinition.parse_raw(json.dumps(default))
    activity.id= clean_name(id)
    activity.url=get_resource_url('ActivityDefinition',id) 

    return activity

def create_activity(activity_definition ,questionnaire):
   #FIXME we should have {{context}} in questionnationnaire to define PATDOC or on the PD
    activity_definition.kind = 'Task'
    #TODO: have std approach for lif ref
    activity_definition.library = [Canonical(get_resource_url('Library',  clean_group_name( clean_name(questionnaire['id']) ))+"|"+get_fhir_cfg().lib_version)]
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
    activity_definition.dynamicValue = [ ActivityDefinitionDynamicValue(
          path = "focus",
          expression = Expression(
              language = "text/cql-identifier",
              expression = "BackReference"
          )
        )
    ]
    new_ext = Extension(
        url = "http://hl7.org/fhir/uv/cpg/StructureDefinition/cpg-collectWith",
        valueCanonical = questionnaire['url'])
    #append_unique(activity_definition.extension, new_ext, True)
    return activity_definition
