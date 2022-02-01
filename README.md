# python fhir sdc generator from xls files

The goal of the project is to have tool like pyxform but for fhir structure data capture

## input file

the input file is an xlsx file with several mandatory sheet



### carePlan

this sheet define the main object that contain the sdc data capture

### pd.<planDefinitionReference>

this sheet defined how the questionnaires are sequences using multiple plan definition, in the cql-tooling it was based on Decision Tables. Here each row will be, an action, that belongs to a main action with a decision ID. If an ID is provided in one row, this will be assumed as main action and the following rows will be assumed as sub actions of this action. If two following rows have the same action, they will be merged into one, joining the inputs with "OR". The delimiter to separate inputs in one action (row) is the pipe (|). 
    
#### id 
    id of the main action

#### description
    - Describe the action to be taken
##### annotation
    - Will be mapped to the textEquivalent in the FHIR resource.  

#### title
    - The title of the action. 

#### applicabilityCondition
    - If this column is filled, the condition mapped with have applicability as type
    
#### startCondition
    - If this column is filled, the condition mapped with have start as type
#### stopCondition
    - If this column is filled, the condition mapped with have stop as type
#### conditionDescription
    - Describes the input that is required for an action to take place
#### conditionExpression
    - The action that will result
#### trigger
    - What will trigger this decision. Must only be specified at the mainAction level
#### triggerType
    - Type of the trigger (named-event | periodic | data-changed | data-accessed | data-access-ended )
#### businessRule
    - Business Rule of the decision 
#### reference
    - Reference for the specific action
#### output
    - The outcome of performing such an action


### q.<questionnaireReference>

thoses sheets are containing the questionnaires, and the required information to de the fihr mapping via structureMap (to be confirmed) and the CQL to find back the answers based on their "label"
the format is inpired by the pyxform 'survey' sheet but addapted to fhir SDC questionnaires



#### id 
    Mandatory, used as linkid

#### type
    - all fhir type but choice : use one of the basic type
    - select_one option : choice when only one selection is possible
    - select_multile option : choice when multiple selections are possible
    - mapping : will not apprear on the questionnaire, just to document mapping information
##### option
        - <valueSetName> valueSet defined in the valueSet tab 
        - url::<valueSetUrl> link to a remote value set
        - candidateExpression::<x-fhir-query> will fetch the result via the <x-fhir-query>, then will dieplay the result based on the data attached to the <candidateExpressionName> in the choiceColum sheet

#### required
    set to True to make sure the question is required

#### display
    dropdown : only for select_one / select_multiple
    <candidateExpressionName> : only for candidateExpression
### valueSet

this sheet define the the valuset that need to be defined in the proejct scope
the format is inpired by the pyxform 'choice' sheet

### choiceColum

this sheet define how candidateExpression result need to be displayed
the format is inpired by the pyxform 'choice' sheet

### cql

this sheet list the additionnal CQL required 

## output files

the output file structure should follow the cqf-tooling structure

## Context

this tool is started to answer WHO EmCare project needs
## Credits

 
pyxform project
cqf-tooling project
