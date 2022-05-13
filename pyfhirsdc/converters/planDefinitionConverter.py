from heapq import merge
import os
import pandas as pd
from fhir.resources.identifier import Identifier
from fhir.resources.fhirtypes import Code

from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.expression import Expression
from fhir.resources.plandefinition import PlanDefinitionAction
from fhir.resources.plandefinition import PlanDefinitionActionCondition
from fhir.resources.relatedartifact import RelatedArtifact
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.triggerdefinition import TriggerDefinition
from datetime import datetime
from datetime import timezone
from fhir.resources.fhirtypes import Canonical

from pyfhirsdc.converters.utils import clean_name



# Merge action conditions as an Or, given that the actions are equal
# condition are consired equal if title and definitionCanonical are equal
# TODO suport equal reference
def mergeActions(previousAction, newAction):
    if previousAction is not None and\
        newAction is not None and\
        previousAction.title == newAction.title and\
        previousAction.definitionCanonical == newAction.definitionCanonical:
        #merge trigger
        if previousAction.trigger is not None and newAction.trigger is not None:
            previousAction.trigger = previousAction.trigger + newAction.trigger
        elif (previousAction.trigger is None or len(previousAction.trigger) == 0)\
            and newAction.trigger is not None:
            previousAction.trigger =  newAction.trigger
        #merge conditions
        if previousAction.condition is not None and newAction.condition is not None:
            previousAction.condition = previousAction.condition + newAction.condition
        elif (previousAction.condition is None or len(previousAction.condition) == 0)\
            and newAction.condition is not None:
            previousAction.condition =  newAction.condition
        return previousAction
    return None
        
        

            



def getIdentifierFirstRep(planDef):
    if (not planDef.identifier):
        identifier = Identifier.construct()
        planDef.identifier = [identifier]
    return planDef.identifier[0]            
    

## function definition from 
# https://hapifhir.io/hapi-fhir//apidocs/hapi-fhir-structures-r4/src-html/org/hl7/fhir/r4/model/PlanDefinition.html#line.4284
## missing in the python library


def write_action_condition(action):
    cql = ""
    if action.description is not None:
        for condition in action.condition:
            ## Output false, manual process to convert the pseudo-code to CQL
            cql += "/*\n \"{0}\":\n ".format(condition.expression.description if condition.expression.description is not None else action.description)+"\n */\n "+\
                "define \"{0}\":\n ".format(condition.expression.expression)+ \
                    "  false" + "\n\n "
    return cql    


def build_plan_definition_index(planDefinitions):
    index =  "### Plan Definitions by Decision ID\n\n "+\
    "|Decision Table|Description| \n "+"|---|---|\n "
    for key, plan_definition in planDefinitions.items():
        index += "|[{0}](PlanDefinition-{1}.html)|{2}|".format(\
            plan_definition.title, plan_definition.id, 
            plan_definition.description)
        index += "\n "
    return index


def write_plan_definition_index(planDefinitions, output_path):
    output = open(output_path+"PlanDefinitionIndex.md", 'w')
    output.write(build_plan_definition_index(planDefinitions))


activityMap = {}
expressionNameCounterMap = {}

## Goes through a row and maps it to FHIR action 
def processAction(row):
    # Check if any of the rows has empty cells in the relevant columns, stop if so
    action = PlanDefinitionAction(
        id = clean_name(row["id"]),
    )
    # input must be better managed
    # https://build.fhir.org/metadatatypes.html#DataRequirement
    # input= row["inputs"]
    action.description = row["description"]
    raw_trigger = row["trigger"]
    if pd.notna(raw_trigger):
        trigger = TriggerDefinition.construct()
        raw_trigger= raw_trigger.split(' ', 1)
        trigger.type =raw_trigger[0]
        trigger.name = raw_trigger[1]
        action.trigger = [trigger]
    # set upd cam
    canonical = row["definitionCanonical"]
    if pd.notna(canonical):
        action.definitionCanonical = Canonical(canonical.replace('{{canonical_base}}', get_fhir_cfg().canonicalBase))
        canonical = row["definitionCanonical"]
 
    title = row["title"]
    if pd.notna(title):
        action.title = title
    
    
    condition = PlanDefinitionActionCondition.construct()
    applicability_condition = row["applicabilityExpressions"]
    if pd.notna(applicability_condition):
        if action.condition is None:
            action.condition = []
        action.condition.append(
            PlanDefinitionActionCondition(
                kind = Code("applicability"),
                expression = Expression(
                    language = "text/cql-expression",
                    expression = applicability_condition.replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)      
                )
            )
        )
    start_condition = row["startExpressions"]
    if pd.notna(start_condition):
        if action.condition is None:
            action.condition = []
        action.condition.append(
            PlanDefinitionActionCondition(
                kind = Code("start"),
                expression = Expression(
                    language = "text/cql-expression",
                    expression = start_condition.replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)      
                )
            )
        )    
    stop_condition = row["stopExpressions"]
    if pd.notna(stop_condition):
        if action.condition is None:
            action.condition = []
        action.condition.append(
            PlanDefinitionActionCondition(
                kind = Code("stop"),
                expression = Expression(
                    language = "text/cql-expression",
                    expression = stop_condition.replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)      
                )
            )
        ) 
    annotation_col = row["annotation"]
    if  pd.notna(annotation_col):
        action.textEquivalent = annotation_col
    
    if not action.documentation: action.documentation = []
    documentation_col = row["documentation"]
    if pd.notna(documentation_col):
        relatedArtifact = RelatedArtifact.construct()
        relatedArtifact.type = "citation"
        relatedArtifact.label = pd.notna(documentation_col)
        action.documentation.append(relatedArtifact)
    return action

def getActivityCoding(activityId, activityCodeSystem):
    global activityMap
    if (not activityId):
        return None
    i = activityId.index(' ')
    if (i <= 1 ):
        return None
    activityCode = activityId[0:i]
    activityDisplay = activityId[i+1:]

    if (not activityCode or not activityDisplay ):
        return None
    
    activity = activityMap.get(activityCode)
    activityCoding = None
    if (not activity):
        activityCoding = Coding.construct()
        activityCoding.code = activityCode
        activityCoding.system = activityCodeSystem
        activityCoding.display = activityDisplay
        activityMap[activityCode] = activityCoding
    return activityCoding

def processDecisionTable(planDefinition, df):
    global expressionNameCounterMap
     ## fetch configuration from the json file ##
    planDefinitionTypeSystem= get_fhir_cfg().PlanDefinition.planDefinitionType.CodeSystem
    planDefinitionTypeCode = get_fhir_cfg().PlanDefinition.planDefinitionType.Code
    planDefinition.date = datetime.now(timezone.utc).isoformat('T', 'seconds')
    planDefinition.experimental = False
    planDefinition.status = "active"

    if not planDefinition.identifier : planDefinition.identifier = []
    if not planDefinition.action : planDefinition.action = []
    coding = Coding.construct()
    coding.code = planDefinitionTypeCode
    coding.system = planDefinitionTypeSystem
    codeableConcept = CodeableConcept.construct()
    codeableConcept.coding = [coding]
    planDefinition.type = codeableConcept
    ## list all the actions with no parents
    planDefinition.action = get_actions(None, df)
    return planDefinition

def get_actions(parentActionId, df):
    if parentActionId is not None and pd.notna(parentActionId):
        df_actions = df[df['parentActionId'] == parentActionId]
    else:
        df_actions = df[df['parentActionId'].isna()]
    actions = []
    if len(df_actions)>0:
        #planDefinition.action = get_actions(parentActionId, df)
        for index, row in df_actions.iterrows():
            current_action = processAction(row)
            if current_action is not None:
                sub_actions = get_actions(current_action.id, df)
                # merge only if no sub action, else add current action on the list
                if sub_actions is not None:
                    current_action.action = sub_actions
                    actions.append(current_action)
                elif len(actions)>0:
                    mergedAction = mergeActions(actions[-1], current_action)
                    if mergedAction is not None:
                        actions[-1] = mergedAction
                    else:
                        actions.append(current_action)
                else:
                    actions.append(current_action)
        return actions
    else:
        return None
    
