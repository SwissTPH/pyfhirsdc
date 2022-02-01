
import json
from pydoc import describe
import re
from ..utils import mergeActions, actionsEqual
from ..converters.to_CQL import generateLibrary
from ..config import get_fhir_cfg, get_processor_cfg
from fhir.resources.expression import Expression
from fhir.resources.plandefinition import PlanDefinition
from fhir.resources.plandefinition import PlanDefinitionAction
from fhir.resources.plandefinition import PlanDefinitionActionCondition
from fhir.resources.relatedartifact import RelatedArtifact
from fhir.resources.identifier import Identifier
from fhir.resources.expression import fhirtypes
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.usagecontext import UsageContext
from fhir.resources.triggerdefinition import TriggerDefinition
from datetime import datetime
import pandas as pd

activityMap = {}
expressionNameCounterMap = {}
planDefinitions = {}


## Goes through a row and maps it to FHIR action 
def processAction(row, input, action_col, 
annotation_col, actionid, currentAnnotationValue, reference_col):
    # Check if any of the rows has empty cells in the relevant columns, stop if so
    if (not row["conditionDescription"] or not row["conditionExpression"] or
     not row["annotation"] ):
        return None
    
    action = PlanDefinitionAction.construct()
    action.id=str(actionid)
    
    if (input==""):
        ## No condition, no action, end of decision table
        return None
    conditionList = input.strip().split('OR')
    applicabilityCondition = ""
    counter = 1
    for condition in conditionList:
        newCondition = "Patient.hasCondition("+condition+")"
        applicabilityCondition += newCondition
        if len(conditionList)!=counter:
            applicabilityCondition += " OR " 
        counter+=1
    applicabilityCondition.replace("|", "AND")
    condition = PlanDefinitionActionCondition.construct()
    expression = Expression.construct()
    expression.language = "text/cql-expression"
    expression.description = applicabilityCondition
    condition.kind = "applicability"
    condition.expression = expression
    action.condition = [condition]
    if not action.action: action.action = []
    actionValues = []

    actions = action_col.strip().split('|')
    for single_action in actions:
        if (pd.notna(action) and pd.notnull(single_action) and single_action):
            actionValues.append(single_action)

    actionsDescription = "AND".join(actionValues)
    action.description = actionsDescription
    #print("ActionValues: ....", actionValues)
    if len(actionValues) == 0:
        action.title = actionValues[0]
    else:
        for actionValue in actionValues:
            subAction = PlanDefinitionAction.construct()
            subAction.title=actionValue
            action.action.append(subAction)
            
    if annotation_col!="":
        if (pd.notna(annotation_col) and pd.notnull(annotation_col) and annotation_col):
            currentAnnotationValue = annotation_col

    action.textEquivalent = currentAnnotationValue
    
    if not action.documentation: action.documentation = []

    if reference_col != "": 
        if (pd.notna(reference_col) and pd.notnull(reference_col) and reference_col):
            relatedArtifact = RelatedArtifact.construct()
            relatedArtifact.type = "citation"
            relatedArtifact.label = reference_col
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
    if (not activity):
        activityCoding = Coding.construct()
        activityCoding.code = activityCode
        activityCoding.system = activityCodeSystem
        activityCoding.display = activityDisplay
        activityMap[activityCode] = activityCoding
    #print("current activityMap: ", activityMap)
    
    return activityCoding

def processDecisionTable(planDefinition, df):
    global expressionNameCounterMap
    canonicalBase = get_fhir_cfg().canonicalBase
     ## fetch configuration from the json file ##
    activityCodeSystem = get_fhir_cfg().activity.CodeSystem
    usageContextSystem = get_fhir_cfg().usageContext.CodeSystem
    usageContextCode = get_fhir_cfg().usageContext.Code
    usageContextDisplay = get_fhir_cfg().usageContext.Display
    planDefinitionTypeSystem= get_fhir_cfg().planDefinition.planDefinitionType.CodeSystem
    planDefinitionTypeCode = get_fhir_cfg().planDefinition.planDefinitionType.Code
    decisionTitle = df[0]["title"]

    print("Decision Title: ", decisionTitle)
    decisionId = df[0]["id"]
    planDefinition.status = "active"
    planDefinition.title = decisionTitle
    identifier = Identifier.construct()
    identifier.use = "oficial"
    identifier.value = df[0]["id"]
    planDefinition.identifier = [identifier]
    planDefinition.name = decisionId
    planDefinition.id = decisionId
    planDefinition.url = canonicalBase + "/PlanDefinition/" + decisionId
    try:
        if (df[0]["businessRule"] != ""):
            decisionDescription = df[0]["businessRule"]
            planDefinition.description = decisionDescription
    except:
        raise ValueError("Expected Business Rule row")

    planDefinition.date = datetime.now()
    planDefinition.experimental = False
    coding = Coding.construct()
    coding.code = planDefinitionTypeCode
    coding.system = planDefinitionTypeSystem
    codeableConcept = CodeableConcept.construct()
    codeableConcept.coding = [coding]
    planDefinition.type = codeableConcept
    try:
        if (df[0]["trigger"] != ""):
            triggerName = df[0]["trigger"]
            planDefinition.description = decisionDescription
    except:
        raise ValueError("Expected Trigger and Trigger description row")
    
    plandefAction = PlanDefinitionAction.construct()
    plandefAction.title = decisionTitle
    triggerDef = TriggerDefinition.construct()
    triggerDef.type = "namedevent"
    triggerDef.name = triggerName
    plandefAction.trigger = [triggerDef]
    planDefinition.action = [plandefAction]

    activityCoding = getActivityCoding(triggerName, activityCodeSystem)
    if (activityCoding != None):
        usageContext = UsageContext.construct()
        usageContextCoding = Coding.construct()
        usageContextCodeableConcept = CodeableConcept.construct()
        usageContextCoding.code = usageContextCode
        usageContextCoding.system = usageContextSystem
        usageContextCoding.display = usageContextDisplay
        usageContextCodeableConcept.coding = [activityCoding]
        usageContext.valueCodeableConcept = usageContextCodeableConcept
        usageContext.code = usageContextCoding
        planDefinition.useContext = [usageContext]

    actionId = 1
    currentAction = PlanDefinitionAction.construct()
    currentAnnotationValue =None
    if not plandefAction.action : plandefAction.action = []
    for i in range(0, len(df)):
        current_main_action_id = df[i]["id"]
        if not pd.notna(current_main_action_id):
            subAction = processAction(df[i], df[i]["conditionDescription"], df[i]["conditionExpression"]\
                , df[i]["annotation"], actionId, currentAnnotationValue, df[i]["reference"])
            if actionsEqual(currentAction, subAction)==False:
                actionId +=1
                print("actionID.............", actionId)
                currentAction = subAction
                nextCounter =1 
                actionDescription = subAction.action[0].title if len(subAction.action) > 1 else subAction.description
                if not actionDescription in expressionNameCounterMap:
                    expressionNameCounterMap[actionDescription] = 1

                nextCounter = expressionNameCounterMap.get(actionDescription)
                expressionNameCounterMap[actionDescription] = nextCounter+1

                actionDescription = actionDescription + (" {0}".format(nextCounter) if nextCounter > 1 else "")
                
                currentAnnotationValue = subAction.textEquivalent
                plandefAction.action.append(subAction)
            else:
                mergeActions(currentAction, subAction)
    return planDefinition

def processDecisionTableSheet(plandef, df ,outputfile):
    libraries ={}
    libraryCQL={}
    """Decision table general format:
        Header rows:
        | Decision ID |
        | Description corresponding to the <Action.Description>  |
        | annotation |
        | Title corresponding to the <Action.title> |
        | applicabilityCondition if it should be mapped as applicability |
        | startCondition if it should be mapped as start condition |
        | stopCondition if it should be mapped as stop Condition |
        | conditionDescription corresponding to the input for the decision |
        | conditionExpression corresponding to the action to be taken |
        | trigger which will correspond to the trigger of the decision |
        | triggerType will represent the type of the trigger for the decision |
        | Business Rule | <Decision Description> |
        | reference of the action to the mentioned output |
        | Output of the particular actino |
        """
    global planDefinitions
    canonicalBase = get_fhir_cfg().canonicalBase
     ## fetch configuration from the json file ##
    scope = get_processor_cfg().scope
    libraryStatus = get_fhir_cfg().library.status
    libraryVersion = get_fhir_cfg().version
    print("------------","Fhir version :",libraryVersion,"-----------")
    
    
    planDefinition=processDecisionTable(plandef,df)
    if pd.notnull(planDefinition):
        planDefinitions[planDefinition.id] =  planDefinition
        libraries, libraryCQL = generateLibrary(planDefinition, canonicalBase, libraryStatus, libraryVersion, scope,libraries,libraryCQL)
    return planDefinitions, libraries, libraryCQL

def convert_df_to_plandefinition(pd, df): 
    libraries ={}
    libraryCQL = {}

