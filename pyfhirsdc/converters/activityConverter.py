import json
import numpy
from fhir.resources.activitydefinition import ActivityDefinition
from pyfhirsdc.config import get_defaut_fhir, get_processor_cfg, get_fhir_cfg
from pyfhirsdc.serializers.json import read_resource
from pyfhirsdc.converters.utils import clean_name, get_custom_codesystem_url, get_resource_url
import pandas as pd

def init_activity(filepath, id):
    activity_json = read_resource(filepath, "Activity")
    default =get_defaut_fhir('Activity')
    if activity_json is not None :
        activity = ActivityDefinition.parse_raw( json.dumps(activity_json))  
    elif default is not None:
        # create file from default
        activity = ActivityDefinition.parse_raw(json.dumps(default))
        activity.id= clean_name(id)
        activity.url=get_resource_url('Activity',id) 

    return activity

def create_activity(activity_definition ,questionnaire):
    activity_definition.id = questionnaire["id"]
    activity_definition.url = get_fhir_cfg().canonicalBase
    activity_definition.experimental = False
    activity_definition.useContext = [{
        "code": {
            "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
            "code": "task",
            "display": "Workflow Task"
    },
    "valueCodeableConcept": {
      "coding": [ {
        "system": get_fhir_cfg().CodeSystem.default.url,
        "code": questionnaire["id"],
        "display": "TOCHANGE"}]}
    }]
    activity_definition.code = {
    "coding" : [
      {
        "system" : "http://hl7.org/fhir/uv/cpg/CodeSystem/cpg-activity-type",
        "code" : "collect-information",
        "display" : "Collect information"
      }
    ]
    }
    activity_definition.dynamicValue = [
    {
      "path" : "input",
      "expression" : {
        "language" : "text/cql-expression",
        "expression" : "{ type: code, value: extension('http://hl7.org/fhir/uv/cpg/StructureDefinition/cpg-collectWith').value }"
      }
    }
    ]
    
    return activity_definition
