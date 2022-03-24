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
from fhir.resources.triggerdefinition import TriggerDefinition
from datetime import datetime
from fhir.resources.fhirtypes import Canonical



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
        planDef.identifier = [identifier]
    return planDef.identifier[0]

def getActionFirstRep(planDef):
    if (not planDef.action):
        action= PlanDefinitionAction.construct()
        planDef.action = [action]
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
                return False
            if actionsEqual(subAction1[i], subAction2[i])==False:
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
def processAction(row):
    # Check if any of the rows has empty cells in the relevant columns, stop if so
    if (not row["inputs"] or not row["description"]):
        return None
    input= row["inputs"]
    action_col = row["description"]
    annotation_col = row["annotation"] if row["annotation"] else ""
    reference_col = row["reference"]
    action = PlanDefinitionAction.construct()
    action.id=row["id"]
    canonical = row["definitionCanonical"]
    raw_trigger = row["trigger"]

    if (input==""):
        ## No condition, no action
        return None
    if pd.notna(raw_trigger):
        trigger = TriggerDefinition.construct()
        raw_trigger= raw_trigger.split(' ', 1)
        trigger.type =raw_trigger[0]
        trigger.name = raw_trigger[1]
        action.trigger = [trigger]
    
    if pd.notna(canonical):
        canonical = Canonical(canonical)
        action.definitionCanonical = canonical

    #Split the conditions with the OR statement so that we can add the cql expression around it
    conditionList = input.strip().split('OR')
    applicability_condition = ""
    counter = 1
    #TODO change the cql expresssions 
    for condition in conditionList:
        if "=" in condition:
            condition = condition.split("=")[1].replace("\\", "" )
            newCondition = "Patient.hasCondition("+condition+")"
        elif "≠" in condition:
            condition = condition.split("≠")[1]
            newCondition = "not Patient.hasCondition("+condition+")"
        applicability_condition += newCondition
        if len(conditionList)!=counter:
            applicability_condition += " OR " 
        counter+=1
    ## In case there are multiple conditions, join them using AND by replacing the pipe
    applicability_condition.replace("|", "AND")
    condition = PlanDefinitionActionCondition.construct()
    expression = Expression.construct()
    expression.language = "text/cql-expression"
    expression.description = applicability_condition
    condition.kind = "applicability"
    condition.expression = expression
    action.condition = [condition]
    #TODO add output to the action? According to the resource it should be DataRequirement
    #output = row["output"]
    #data_req = DataRequirement.construct()
    #action.output = [output]
    if not action.action: action.action = []
    actionValues = []

    actions = action_col.strip().split('|')
    for single_action in actions:
        if (pd.notna(action) and pd.notnull(single_action) and single_action):
            actionValues.append(single_action)
    ## Join the values that were split by the PIPE with AND
    actions_description = "AND".join(actionValues)
    action.description = actions_description
    if len(actionValues) == 1:
        action.title=actionValues[0]
    else:
        for actionValue in actionValues:
            subAction = PlanDefinitionAction.construct()
            subAction.title=actionValue
            action.action.append(subAction)

    if annotation_col!="":
        if (pd.notna(annotation_col) and pd.notnull(annotation_col) and annotation_col):
            action.textEquivalent = annotation_col
    
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
    planDefinition.date = datetime.now()
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
    orphan_actions = df[df['parentActionId'].isna()].id.values.tolist()
    plandefinition_actions = []
    for orphan in orphan_actions:
        initial_plandefinition_action = PlanDefinitionAction.construct()
        actions = get_actions(orphan, df, initial_plandefinition_action)
        plandefinition_actions.append(actions)
    planDefinition.action = plandefinition_actions
    return planDefinition

def get_actions(parentActionId, df, plandef_action):
    actions = df[df['parentActionId'] == parentActionId].to_dict('index')
    processedActions = []
    ## fecth the parent row
    mainActionRow = (df[df['id'] == parentActionId].to_dict('records'))
    if plandef_action.action ==None : plandef_action.action = []
    if pd.notna(mainActionRow):
        mainAction = processAction(mainActionRow[0])
        print("Processing main action: {0} and its children .........".format(mainAction.id))
        processedActions.append(mainAction)
        plandef_action.action.append(mainAction)
    #planDefinition.action = get_actions(parentActionId, df)
    current_action = PlanDefinitionAction.construct()
    for key, action in actions.items():
        ## if the action has both a parent ID and an ID it means it is both a parent and a child -> recursive; 
        ## We do not add the action right here because we add it outside of this loop, as a main action
        if not '.' in action["id"] and pd.notna(action["parentActionId"]):
            get_actions(action["id"], df, plandef_action)
        ## If we do have a sub id in the ID AND a parant then we are talking about a child -> attach the action
        elif '.' in action["id"] and pd.notna(action["parentActionId"]):
            action = processAction(action)
            if actionsEqual(current_action, action) == False:
                current_action = action
                sub_plandef_action = PlanDefinitionAction.construct()
                sub_plandef_action.action = [action]
                plandef_action.action.append(sub_plandef_action)
            else :
                mergeActions(current_action, action)
    return plandef_action
