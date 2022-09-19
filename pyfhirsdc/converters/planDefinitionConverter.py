import pandas as pd
from fhir.resources.fhirtypes import Code
from pyfhirsdc.config import get_fhir_cfg
from fhir.resources.expression import Expression
from fhir.resources.plandefinition import PlanDefinitionAction, PlanDefinitionActionRelatedAction, PlanDefinitionActionCondition
from fhir.resources.relatedartifact import RelatedArtifact
from fhir.resources.triggerdefinition import TriggerDefinition
from fhir.resources.fhirtypes import Canonical
from pyfhirsdc.converters.utils import  clean_name, get_codableconcept_code, init_list, init_resource_meta
from ..serializers.librarySerializer import ROW_EXPRESSIONS





## Goes through a row and maps it to FHIR action 
def process_action(row):
    # Check if any of the rows has empty cells in the relevant columns, stop if so
    action = PlanDefinitionAction(
        id = clean_name(row["id"]),
        description = value_not_na(row["description"]),
        definitionCanonical = Canonical(row["definitionCanonical"].replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)) if pd.notna(row["definitionCanonical"]) else None,
        title = value_not_na(row["title"]),
        trigger = get_triggers(row),
        condition = get_conditions(row),
        textEquivalent = value_not_na(row["annotation"]),
        documentation = get_documentation(row),
        relatedAction = get_related_actions(row),
        type = get_cpg_comon_process_type(row)
    )
    # input must be better managed
    # https://build.fhir.org/metadatatypes.html#DataRequirement
    # input= row["inputs"]
    return action

CPG_COMMON_PROCESSES = [
    "registration", 
    "triage", 
    "local-urgent-care", 
    "history-and-physical", 
    "provide-counseling", 
    "diagnostic-testing", 
    "determine-diagnosis", 
    "guideline-based-care", 
    "dispense-medications", 
    "emergency-care", 
    "actue-tertiary-care", 
    "charge-for-service", 
    "discharge-referral-of-patient", 
    "record-and-report", 
    "monitor-and-follow-up-of-patient", 
    "alerts-reminders-education"
]

def get_cpg_comon_process_type(row):
    if pd.notna(row["type"]) and row["type"] in CPG_COMMON_PROCESSES:
        return get_codableconcept_code(
            'http://hl7.org/fhir/uv/cpg/CodeSystem/cpg-common-process', 
            row["type"])
         

def get_related_actions(row):
    related_actions = []
    if pd.notna(row["relatedAction"]):
        actions = row["relatedAction"].split('||')
        for action in actions:
            details = action.split('::')
            if len(details) == 2:
                related_actions.append(PlanDefinitionActionRelatedAction(
                    relationship = details[0].strip(),
                    actionId = details[1].strip()
                ))
            else:
                print("Warning, {} related action is not correct, it should follow that format type::id(||type::id)*".format(row['id']))
    return     related_actions
    
def get_documentation(row):
    documentation_col = row["documentation"]
    if pd.notna(documentation_col):
        relatedArtifact = RelatedArtifact.construct()
        relatedArtifact.type = "citation"
        relatedArtifact.label = documentation_col
        return [relatedArtifact]

def value_not_na(value):
    if pd.notna(value):
        return value

def get_triggers(row):
    raw_trigger = row["trigger"]
    if pd.notna(raw_trigger):
        trigger = TriggerDefinition.construct()
        raw_trigger= raw_trigger.split(' ', 1)
        trigger.type =raw_trigger[0]
        trigger.name = raw_trigger[1]
        return [trigger]

        
def get_conditions(row):
    condition = []
    for name, exp in ROW_EXPRESSIONS.items():
        if name is not 'id' and name in row and pd.notna(row[name]):
            condition.append( PlanDefinitionActionCondition(
                kind = Code(exp['kind']),
                expression = Expression(
                    language = "text/cql-identifier",
                    expression = exp['prefix']+row['id'],
                    description =    row[name].replace('{{canonical_base}}', get_fhir_cfg().canonicalBase)     
                )
            ))
    if len(condition)>0:
        return condition
 
def process_decisiontable(planDefinition, df):
     ## fetch configuration from the json file ##
    init_resource_meta(planDefinition)
    init_list(planDefinition.identifier) 
    planDefinition.type = get_codableconcept_code( 
        get_fhir_cfg().PlanDefinition.planDefinitionType.CodeSystem,
        get_fhir_cfg().PlanDefinition.planDefinitionType.Code
    )
    ## list all the actions with no parents
    planDefinition.action = get_actions(None, df)
    return planDefinition

def get_actions(parent_action_id, df):
    if parent_action_id is not None and pd.notna(parent_action_id):
        df_actions = df[df['parentId'] == parent_action_id]
    else:
        df_actions = df[df['parentId'].isna()]
    actions = []
    if len(df_actions)>0:
        #planDefinition.action = get_actions(parent_action_id, df)
        for index, row in df_actions.iterrows():
            current_action = process_action(row)
            if current_action is not None:
                sub_actions = get_actions(current_action.id, df)
                # merge only if no sub action, else add current action on the list
                if sub_actions is not None:
                    current_action.action = sub_actions
                    actions.append(current_action)
                else:
                    actions.append(current_action)
        return actions
    else:
        return None
    
