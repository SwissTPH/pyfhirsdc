import logging

from pyfhirsdc.converters.utils import adv_clean_name
from pyfhirsdc.models.mapping import MappingGroup, MappingGroupIO, MappingRule

logger = logging.getLogger("default")
### create related person
# args[0] linkid for relatedPerson
def SetCommunicationRequest(mode, profile, question_id,df_questions,*args):
    rule_name = adv_clean_name(profile+question_id)
    id_prefix = adv_clean_name(profile)
    if mode == 'rules':
        return None
    elif mode == 'groups':
        return [MappingGroup(
            name = rule_name,
            sources = [MappingGroupIO(name = 'src')],
            targets = [MappingGroupIO(name = 'tgt')],
            rules = [
                #MappingRule(name = 'cat', expression = "src -> tgt.category = cc('http://terminology.hl7.org/CodeSystem/communication-category', 'notification')"),
                MappingRule(expression = "src ->  tgt.category = create('CodeableConcept') as cc, cc.coding = create('Coding') as c, c.system ='http://hl7.org/fhir/ValueSet/communication-category', c.code = 'notification'"),
                #MappingRule(name = 'pd', expression = "src -> tgt.status = 'active', tgt.basedOn = src.basedOn".format( inject_config(args[0]))),
                MappingRule(name = 'quest', expression = "src.questionnaire as q ->   tgt.about = create('Reference') as ref, ref.type ='Questionnaire', ref.reference = q"),
                MappingRule(expression = "src.subject as subject ->   tgt.subject = subject "),
                MappingRule(expression = "src ->   tgt.recipient =create('Reference') as ref ",
                    rules = [
                        MappingRule( expression = "src -> ref.type = 'RelatedPerson'" ),
                        MappingRule(
                expression = "src.item first as item where linkId  =  '{0}' -> tgt".format(args[0]),
                rules = [MappingRule( 
                            expression  ="item.answer first as a ->  tgt", 
                            rules = [MappingRule(expression="a.value as val ->  ref.reference = append('/RelatedPerson/', val)")])])
                    ])
                
            ],  

        )]
    elif mode == 'docs':
        return   {
            'type' : 'CommunicationRequest',
            'code' : question_id,
            'valueType' : 'N/A',
            'description': 'set a communication request to the care giver'
        }

    
    