import os
import pandas as pd
from fhir.resources.identifier import Identifier


from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.expression import Expression
from fhir.resources.plandefinition import PlanDefinitionAction
from fhir.resources.plandefinition import PlanDefinitionActionCondition
from fhir.resources.relatedartifact import RelatedArtifact
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.usagecontext import UsageContext
from fhir.resources.triggerdefinition import TriggerDefinition
from datetime import datetime


from pyfhirsdc.utils import write_resource

# Merge action conditions as an Or, given that the actions are equal
def mergeActions(currentAction, newAction):
    currentCondition = getConditionFirstRep(currentAction)
    newCondition = getConditionFirstRep(newAction)
    if not pd.notnull(currentCondition):
        currentAction.condition += newCondition
    elif pd.notnull(newCondition):
        currentCondition.expression.description = "({0})\n  OR ({1})".format(currentCondition.expression.description, newCondition.expression.description)
## function definition from 
# https://hapifhir.io/hapi-fhir//apidocs/hapi-fhir-structures-r4/src-html/org/hl7/fhir/r4/model/PlanDefinition.html#line.4284
## missing in the python library


def getConditionFirstRep(action):
    if (not action.condition):
        condition = PlanDefinitionActionCondition.construct()
        action.condition = [condition]
    return action.condition[0]

def getIdentifierFirstRep(planDef):
    if (not planDef.identifier):
        identifier = Identifier.construct()
        planDef.identifier = identifier
    return planDef.identifier[0]

def getActionFirstRep(planDef):
    if (not planDef.action):
        action= PlanDefinitionAction.construct()
        planDef.action = action
    return planDef.action[0]

def actionsEqual(currentAction, newAction):
    ## If currentAction is None we're just starting 
    if (currentAction.action ==None and newAction.action ==None):
        return True
    elif (currentAction.action ==None and newAction.action !=None):
        return False
    #print("currentAction: ", currentAction)
    currentActionSubs = PlanDefinitionAction.construct()
    currentActionSubs.action = currentAction.action
    newActionSubs = PlanDefinitionAction.construct()
    newActionSubs.action = newAction.action

    currentActionDescription = ""
    if currentActionSubs.action!=None:
        for action in currentActionSubs.action:
            if currentActionDescription !="":
                currentActionDescription += " AND " + action.title 
            elif action.title is not None:
                currentActionDescription += action.title

    newActionDescription = ""
    if newActionSubs.action!=None:
        for action in newActionSubs.action:
            if newActionDescription !="":
                newActionDescription += " AND " + action.title 
            elif  action.title is not None:
                newActionDescription += action.title
    
    print("currentTitle: ", currentAction.title == newAction.title)
    print("currentText: ", currentAction.textEquivalent == newAction.textEquivalent)
    print("currentDescription: ", currentActionDescription == newActionDescription)
    print("currentDescription: ", currentActionDescription, "... and new description: ",newActionDescription)
    print(subActionsEqual(currentAction.action, newAction.action))
    return ((currentAction.title == newAction.title) and 
    (currentAction.textEquivalent == newAction.textEquivalent) and
    (currentActionDescription == newActionDescription) and subActionsEqual(currentAction.action, newAction.action))


def subActionsEqual(subAction1,subAction2):
    # Check if list of actions is equal
    if subAction1==None and subAction2==None:
        return True
    if subAction1!=None and subAction2!=None :
        for i in range(len(subAction1)):
            if i >= len(subAction2):
                print("Not the same size...")
                return False
            if actionsEqual(subAction1[i], subAction2[i])==False:
                print("Not the same action...")
                #print("subAction 1 is : ", subAction1[i], "\n not equal to subAction2 : ", subAction2[i] )
                return False
    return True




def write_action_condition(action):
    condition = getConditionFirstRep(action)
    if (not pd.isnull(condition.expression.expression)):
        condition.expression.expression = "Should {0}".format(action.description.replace("\"", "\\\"") \
            if action.description else "perform action")
    
    ## Output false, manual process to convert the pseudo-code to CQL
    return "/*\n "+getConditionFirstRep(action).expression.description+"\n */\n "+\
        "define \"{0}\":\n ".format(getConditionFirstRep(action).expression.expression)+ \
            "  false" + "\n\n "





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
def processAction(row, actionid, currentAnnotationValue):
    input= row["conditionDescription"]
    action_col = row["conditionExpression"]
    annotation_col = row["annotation"]
    reference_col = row["reference"]
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
        if "=" in condition:
            condition = condition.split("=")[1]
            newCondition = "Patient.hasCondition("+condition+")"
        elif "≠" in condition:
            print("inequality")
            condition = condition.split("≠")[1]
            newCondition = "not Patient.hasCondition("+condition+")"
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
    #TODO add output to the action? According to the resource it should be DataRequirement
    #output = row["output"]
    #action.output = [output]
    if not action.action: action.action = []
    actionValues = []

    actions = action_col.strip().split('|')
    for single_action in actions:
        if (pd.notna(action) and pd.notnull(single_action) and single_action):
            actionValues.append(single_action)

    actionsDescription = "AND".join(actionValues)
    action.description = actionsDescription
    #print("ActionValues: ....", actionValues)
    #FIXEME title is always None
    if len(actionValues) == 0:
        action.title=actionValues[0]
    else:
        for actionValue in actionValues:
            subAction = PlanDefinitionAction.construct()
            action.title=actionValue
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
    planDefinitionTypeSystem= get_fhir_cfg().PlanDefinition.planDefinitionType.CodeSystem
    planDefinitionTypeCode = get_fhir_cfg().PlanDefinition.planDefinitionType.Code
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
    triggerDef.type = df[1]["trigger"]
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
            subAction = processAction(df[i], actionId, currentAnnotationValue)
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
                if actionDescription is None:
                        actionDescription= " "
                actionDescription = actionDescription + (" {0}".format(nextCounter) if nextCounter > 1 else "")
                
                currentAnnotationValue = subAction.textEquivalent
                plandefAction.action.append(subAction)
            else:
                mergeActions(currentAction, subAction)
    return planDefinition
