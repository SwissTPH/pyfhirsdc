
import json
from pydoc import describe
import sys, getopt, os
import string
from pydantic import BaseModel
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

def processAction(row, inputColidx, outputColidx, actionColidx, 
annotationColidx, actionid, currentAnnotationValue, refColidx):
    # Check if any of the rows has empty cells in the relevant columns, stop if so
    if (not row.iloc[0][inputColidx] or not row.iloc[0][actionColidx] or
     not row.iloc[0][annotationColidx] ):
        return None
    
    action = PlanDefinitionAction.construct()
    action.id=str(actionid)

    conditionValues = []
    #Go through every element of the row between input and output column
    for i in range(inputColidx,outputColidx):
        inputCondition = row[i]
        if (pd.notna(inputCondition) and pd.notnull(inputCondition) and inputCondition):
            conditionValues.append(inputCondition)
    
    if (len(conditionValues) ==0):
        ## No condition, no action, end of decision table
        return None

    applicabilityCondition = ""
    if len(conditionValues) == 1:
        applicabilityCondition + conditionValues[0]
    else:
        for value in conditionValues:
            if len(applicabilityCondition) > 0:
                applicabilityCondition += "\n  AND  "
            applicabilityCondition += "("
            applicabilityCondition += value
            applicabilityCondition += ")"

    condition = PlanDefinitionActionCondition.construct()
    expression = Expression.construct()
    expression.language = "text/cql-identifier"
    expression.description = applicabilityCondition
    condition.kind = "applicability"
    condition.expression = expression
    action.condition = condition

    actionValues = []

    for i in range(actionColidx, annotationColidx):
        actionValue = row[i]
        if (pd.notna(actionValue) and pd.notnull(actionValue) and actionValue):
            actionValues.append(actionValue)

    actionsDescription = " AND ".join(actionValues)
    action.description = actionsDescription
    
    action.title = actionValues[0]

    if len(actionValues) > 1:
        for actionValue in actionValues:
            subAction = PlanDefinitionAction.construct()
            subAction.title=actionValue
            action.action += subAction
            
    if annotationColidx >= 0:
        annotationValue = row[i]
        if (pd.notna(annotationValue) and pd.notnull(annotationValue) and annotationValue):
            currentAnnotationValue = annotationValue
    # Comment by original team : TODO: Might not want to duplicate this so much?
    # NOt sure what is meant with it
    action.textEquivalent = currentAnnotationValue
    

    # TODO: Link this to the RelatedArtifact for References

    if refColidx >= 0: 
        referenceValue = row[i]
        if (pd.notna(referenceValue) and pd.notnull(referenceValue) and referenceValue):
            relatedArtifact = RelatedArtifact.construct()
            relatedArtifact.type = "citation"
            action.documentation += relatedArtifact
    
    return action

def actionsEqual(currentAction, newAction):
    if (not pd.notna(currentAction) and not pd.notnull(currentAction)):
        return False
    
    currentActionSubs = PlanDefinitionAction.construct()
    currentActionSubs.action = currentAction.action
    newActionSubs = PlanDefinitionAction.construct()
    newActionSubs.action = newAction.action

    currentActionDescription =" AND ".join(currentActionSubs)
    newActionDescription =" AND ".join(newActionSubs)

    return ((currentAction.title == newAction.title) and 
    (currentAction.textEquivalent == newAction.textEquivalent) and
    (currentActionDescription == newActionDescription) and 
    (subActionsEqual(currentAction.action, newAction.action)))


def subActionsEqual(subAction1,subAction2):
    # Check if list of actions is equal
    if pd.notna(subAction1) and pd.notna(subAction2):
        return True
    
    for i in range(len(subAction1)):
        if i >= len(subAction2):
            return False
        if not actionsEqual(subAction1[i], subAction2[i]):
            return False

    return True



def getActivityCoding(activityId, activityCodeSystem):
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
    
    return activityCoding

def processDecisionTable(df, canonicalBase, activityCodeSystem, usageContextSystem, 
usageContextCode, usageContextDisplay, planDefinitionTypeSystem, planDefinitionTypeCode):
    planDefinition = PlanDefinition.construct()
    decisionTitle = df.columns[1].strip()
    decisionTitle_idx = df.columns.get_loc(df.columns[1])
    print(decisionTitle)
    try:
        ## Check if we have a business rule specified
        index = decisionTitle.index(' ')
        decisionIdentifier = decisionTitle[0:index]
    except:
        raise ValueError("Expected business rule title of the form '<ID> <Title>'")
    decisionId = decisionIdentifier.replace(".","")
    planDefinition.status = "active"
    planDefinition.title = decisionTitle
    identifier = Identifier.construct()
    identifier.use = "oficial"
    identifier.value = decisionIdentifier
    planDefinition.identifier = [identifier]
    planDefinition.name = decisionId
    planDefinition.id = decisionId
    planDefinition.url = canonicalBase + "/PlanDefinition/" + decisionId
    try:
        if (df.iloc[0][0] == "Business Rule"):
            decisionDescription = df.iloc[0][1]
            planDefinition.description = decisionDescription
    except:
        raise ValueError("Expected Business Rule row")

    planDefinition.date = datetime.now()
    planDefinition.experimental = False
    coding = Coding.construct()
    coding.code = planDefinitionTypeCode
    coding.system = planDefinitionTypeSystem
    planDefCoding = coding
    codeableConcept = CodeableConcept.construct()
    codeableConcept.coding = [coding]
    planDefinition.type = codeableConcept
    try:
        if (df.iloc[1][0] == "Trigger"):
            triggerName = df.iloc[1][1]
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

    # print(df.iloc[2])
    cols_nr = df.shape[1]
    #print(df.to_json())
    for i in range(cols_nr):
        decisionHeader = df.iloc[2][i]
        if pd.isna(decisionHeader):
            continue
        elif (decisionHeader).lower() == "input" or (decisionHeader).lower() == "inputs":
            inputColIdx = i 
        
        elif (decisionHeader).lower() == "output" or (decisionHeader).lower() == "outputs":
            outputColIdx = i 
            
        elif (decisionHeader).lower() == "action" or (decisionHeader).lower() == "actions":
            actionsColIdx = i 
        
        elif (decisionHeader).lower() == "annotation(s)" or (decisionHeader).lower() == "annotations":
            annotationsColIdx = i 
        
        elif (decisionHeader).lower() == "reference(s)" or (decisionHeader).lower() == "references":
            refColIdx = i
            break
    
    actionId = 1
    currentAction = PlanDefinitionAction.construct()
    currentAnnotationValue =None
    for i in range(3, len(df)):
        subAction = processAction(df.iloc[i], inputColIdx, outputColIdx, actionsColIdx,
        annotationsColIdx, actionId, currentAnnotationValue, refColIdx)

        if subAction == None:
            break

        if not actionsEqual(currentAction, subAction):
            actionId +=1
            currentAction = subAction
            nextCounter =1 
            actionDescription = subAction.action[0].title if len(subAction.action) > 1 else subAction.description
            if not actionDescription in expressionNameCounterMap:
                expressionNameCounterMap[actionDescription] = 1

            nextCounter = expressionNameCounterMap.get(actionDescription)
            expressionNameCounterMap[actionDescription] = nextCounter+1

            actionDescription = actionDescription + (" {0}".format(nextCounter) if nextCounter > 1 else "")
            
            currentAnnotationValue = subAction.textEquivalent
            plandefAction.action += subAction
        else:
            mergeActions(currentAction, subAction)
    
    print(activityCoding)
    print(planDefinition.json())
    return planDefinition

# Merge action conditions as an Or, given that the actions are equal
def mergeActions(currentAction, newAction):

    currentCondition = getConditionFirstRep(currentAction)
    newCondition = getConditionFirstRep(newAction)
    if not pd.notnull(currentCondition):
        currentAction.action += newCondition
    elif pd.notnull(newCondition):
        currentCondition.expression.description = "({0})\n  OR ({1})".format(currentCondition.expression.description, newCondition.expression.description)
## function definition from 
# https://hapifhir.io/hapi-fhir//apidocs/hapi-fhir-structures-r4/src-html/org/hl7/fhir/r4/model/PlanDefinition.html#line.4284
## missing in the python library

def getConditionFirstRep(action):
    if (not action.condition):
        condition = PlanDefinitionActionCondition.construct()
        action.condition = [action]
    return action.condition[0]

def generateLibrary(plandefinition):
    return


def processDecisionTableSheet(inputfile, dsn, conf ,outputfile):
    """Decision table general format:
        Header rows:
        | Decision ID | <Decision ID> <Decision Title> |
        | Business Rule | <Decision Description> |
        | Trigger | <Workflow Step Reference> |
        | Input(s) | ... | Output | Action | Annotation | Reference |
        | <Condition> | ... | <Action.Description> | <Action.Title> |
        | <Action.TextEquivalent> | <Action.Document> | --> Create a row for each...
        """

    file = open(conf)
    json_conf = json.load(file)
    file.close()
    canonicalBase = json_conf["canonicalBase"]
    skiprows = json_conf["skiprows"]
    skipcols=json_conf["skipcols"]
    activityCodeSystem = json_conf["activityCodeSystem"]
    usageContextSystem = json_conf["usageContextSystem"]
    usageContextCode = json_conf["usageContextCode"]
    usageContextDisplay = json_conf["usageContextDisplay"]
    planDefinitionTypeSystem= json_conf["planDefinitionTypeSystem"]
    planDefinitionTypeCode = json_conf["planDefinitionTypeCode"]
    if not os.path.exists(outputfile):
        os.makedirs(outputfile)
    individual_dsn = dsn.split(',')
    for sheet in individual_dsn:
        df = pd.read_excel(inputfile, sheet_name=sheet, skiprows=skiprows)
        if (skipcols == 1):
            df.drop(df.columns[[0]], axis=1, inplace=True)
        elif (skipcols > 1 ):
            df.drop(df.columns[[0,skipcols-1]], axis=1, inplace = True)
        
        if(df.columns[0].lower().startswith("decision")):
            json_df = df.apply(lambda x: x.to_json(), axis=1)
            planDefinition=processDecisionTable(df, canonicalBase, activityCodeSystem, 
            usageContextSystem, usageContextCode, usageContextDisplay,
            planDefinitionTypeSystem, planDefinitionTypeCode)
            if pd.notnull(planDefinition):
                planDefinitions[planDefinition.id, planDefinition]
                generateLibrary(planDefinition)
            break

if __name__ == "__main__": 
    try:
      opts, args = getopt.getopt(sys.argv[1:],"hi:d:c:o:",["ifile=","dsn=","conf=","ofile="])
    except getopt.GetoptError:
        print('main.py -i <inputfile> -d <datadictionarysheetnames> -c <configfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -i <inputfile> -d <datadictionarysheetnames> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-d", "--dsn"):
            dsn = arg
        elif opt in ("-c", "--conf"):
            conf = arg
    processDecisionTableSheet(inputfile,dsn,conf,outputfile="./output") # output is the default output directory

