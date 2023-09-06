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
    activity_definition = ActivityDefinition.parse_raw(json.dumps(get_defaut_fhir('ActivityDefinition')))
    activity_definition.url=get_resource_url('ActivityDefinition',act_id) 
    activity_definition.kind = 'Task'
    activity_definition.id = act_id
    #TODO: have std approach for lif ref
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


def create_activity_propose_diagnosis(row,library):
    activity_definition = ActivityDefinition.parse_raw(json.dumps(get_defaut_fhir('ActivityDefinition-propose-diagnosis')))
    activity_definition.dynamicValue.append(
        ActivityDefinitionDynamicValue(
            path= "input:diagnosis",
            expression= Expression(
            language = "text/cql-identifier",
            expression = "TaskInput {"+
                "type: 'propose-diagnosis',"+
                'value: Condition {'+
                    'clinicalStatus: pfsdc."Active",'
                    'verificationStatus: pfsdc."Provisional",'
                    f"code: [cond.\"{row['id']}\"],"+ 
                    'subject: pfsdc.getPatientReference,'+ 
                    'encounter: pfsdc.getEncounterReference,'+ 
                    'onsetDateTime: Today(),'+
                    f"extensions: getPostCordination_{row['id']}"+
                "}"+
            "}")
        )
    )
    activity_definition.id= clean_name('propose-diagnosis-' + row['id'])
    activity_definition.url=get_resource_url('ActivityDefinition',activity_definition.id)
    activity_definition.library = [library.url+"|"+Canonical(library.version)]
    return activity_definition
