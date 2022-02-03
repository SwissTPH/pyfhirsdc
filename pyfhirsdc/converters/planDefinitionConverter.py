import os
import pandas as pd
from pyfhirsdc.config import get_fhir_cfg, get_processor_cfg
from fhir.resources.plandefinition import PlanDefinitionAction
from fhir.resources.plandefinition import PlanDefinitionActionCondition
from fhir.resources.identifier import Identifier

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
            else:
                currentActionDescription += action.title

    newActionDescription = ""
    if newActionSubs.action!=None:
        for action in newActionSubs.action:
            if newActionDescription !="":
                newActionDescription += " AND " + action.title 
            else:
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




def write_action_condition(cql, action):
    condition = getConditionFirstRep(action)
    if (not pd.isnull(condition.expression.expression)):
        condition.expression.expression = "Should {0}".format(action.description.replace("\"", "\\\"") \
            if action.description else "perform action")
    
    ## Output false, manual process to convert the pseudo-code to CQL
    cql+= "/*\n "+getConditionFirstRep(action).expression.description+"\n */\n "+\
        "define \"{0}\":\n ".format(getConditionFirstRep(action).expression.expression)+ \
            "  false" + "\n\n "

def write_plan_definitions(plandefinitions,encoding,outputpath):
    if pd.notnull(plandefinitions) and len(plandefinitions)>0:
        for key, value in plandefinitions.items():
            if (os.path.exists(outputpath)):
                write_resource(outputpath, value, encoding)
            else:
                raise ValueError("The validity of the path could not be established")



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

