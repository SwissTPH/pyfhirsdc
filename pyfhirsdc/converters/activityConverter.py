import json
from fhir.resources.activitydefinition import ActivityDefinition, ActivityDefinitionDynamicValue
from fhir.resources.usagecontext import  UsageContext 
from fhir.resources.expression import  Expression
from fhir.resources.extension import Extension
from pyfhirsdc.config import get_defaut_fhir
from .extensionsConverter import append_unique
from pyfhirsdc.serializers.json import read_resource
from pyfhirsdc.converters.utils import clean_name, get_codableconcept_code, get_code, get_custom_codesystem_url, get_resource_url

def init_activity(filepath, id):
    activity_json = read_resource(filepath, "ActivityDefinition")
    default =get_defaut_fhir('ActivityDefinition')
    if activity_json is not None :
        activity = ActivityDefinition.parse_raw( json.dumps(activity_json))  
    elif default is not None:
        # create file from default
        activity = ActivityDefinition.parse_raw(json.dumps(default))
        activity.id= clean_name(id)
        activity.url=get_resource_url('ActivityDefinition',id) 

    return activity

def create_activity(activity_definition ,questionnaire):
    activity_definition.useContext = [
      UsageContext( 
        code = get_code(
          "http://terminology.hl7.org/CodeSystem/usage-context-type", 
          "task"),
        valueCodeableConcept = get_codableconcept_code(
          get_custom_codesystem_url(), 
          questionnaire["id"],
          "Collect infornation with questionnaire {}".format(questionnaire['title'])))
    ]
    activity_definition.code = get_codableconcept_code(
      "http://hl7.org/fhir/uv/cpg/CodeSystem/cpg-activity-type",
      "collect-information",
      "Collect information")
    # could nbe splitted into input.code / input.value
    activity_definition.dynamicValue = [ ActivityDefinitionDynamicValue(
        path = "input",
        expression = Expression(
            language = "text/cql-expression",
            expression = "{ type: code, value: extension('http://hl7.org/fhir/uv/cpg/StructureDefinition/cpg-collectWith').value }"
      )
    )]
    new_ext = Extension(
        url = "http://hl7.org/fhir/uv/cpg/StructureDefinition/cpg-collectWith",
        valueCanonical = questionnaire['url'])
    append_unique(activity_definition.extension, new_ext, True)
    return activity_definition
