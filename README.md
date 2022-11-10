# Python FHIR SDC generator from XLS/ODS files

The goal of the project is to have tool like pyxform but for fhir structure data capture

## input file

the input file is an xlsx file with several mandatory sheet


## Config file

the config file is a json with two main section 

processor;
```
"processor":{
        "inputFile":"/home/<>/WHO DAK/merged/xls_form_iraq.xlsx",
        "manual_content":"/home/<>/smart-emcare/manual",
        "outputPath":"/home/<>/smart-emcare/input",
        "cql_translator": "https://fhir.cql-translator.dk.swisstph-mis.ch/cql/translator",
        "mapping_translator": "https://fhir.dk.swisstph-mis.ch/matchbox/fhir/StructureMap",
        "default_resource_path":"./default_resources",
        "excudedWorksheets":[
        ],
        "scope":"EmCare",
        "encoding":"json",
        "generateElm" : false
    },

```

FHIR:
```
"fhir":{
        "version": "4.0.1",
        "lib_version": "0.99.99",
        "canonicalBase" : "https://fhir.dk.swisstph-mis.ch/matchbox/fhir/",
        "guideBase":"http://fhir.org/guides/who/emc-cds/",
        "activity":{
            "CodeSystem": "http://fhir.org/guides/who/anc-cds/CodeSystem/activity-codes"
        },
        "external_libraries" : {
            "FHIRHelpers" : "http://fhir.org/guides/who/anc-cds/Library/FHIRHelpers"
        }
        ,
        "usageContext":{
            "CodeSystem": "http://terminology.hl7.org/CodeSystem/usage-context-type",
            "Code": "task",
            "Display": "Workflow Task"
        },
        "PlanDefinition":{
            "outputPath":"resources/plandefinition",
            "planDefinitionType":{
                "CodeSystem": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
                "Code": "eca-rule"
            }
        },
        "Extensions":{
            "outputPath":"resources/extensions"
        },
        "Profiles": {
            "outputPath":"profiles"
        },
        "Questionnaire":{
            "outputPath":"resources/questionnaire"
        },
        "ActivityDefinition":{
            "outputPath":"resources/activitydefinition"
        },
        "Library":{
            "outputPath":"resources/library/"
        },
        "Bundle":{
            "outputPath" : "bundles"
        },
        "pagecontent":{
            "outputPath":"/pagecontent/"
        },"CodeSystem":
        {
            "outputPath":"vocabulary/codesystem/"
        },"ValueSet":
        {
            "outputPath":"vocabulary/valueset/"
        }
    }
```


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
#### constraintDescription
    - Describes the input that is required for an action to take place
#### constraintExpression
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
### l. libraries

will create a library, same way and fields as the questionnaire


### q.<questionnaireReference>

thoses sheets are containing the questionnaires, and the required information to de the fihr mapping via structureMap (to be confirmed) and the CQL to find back the answers based on their "label"
the format is inpired by the pyxform 'survey' sheet but addapted to fhir SDC questionnaires



#### id 
Mandatory, used as linkid

#### type
will follow the structure [type] [option]

##### type
- all fhir type but choice : use one of the basic type
- select_one option : choice when only one selection is possible
- select_multile option : choice when multiple selections are possible
- mapping : will not apprear on the questionnaire, just to document mapping information
- group start: will start a question group, an ID is mandatory, several levels are possible
- group end: will end a question group, an ID is mandatory
- variable : add a variable in the questionnaire, on the questionnaire level if no parentId is specified, else on the question where id == parentId, the expression MUST be in calcualtedExpression column

##### option
- [valueSetUrl] valueSet defined in the valueSet tab 
- url::[valueSetUrl] link to a remote value set
- candidateExpression::<x-fhir-query> will fetch the result via the <x-fhir-query>, then will dieplay the result based on the data attached to the <candidateExpressionName> in the choiceColum sheet

#### required
set to True to make sure the question is required

#### display

can be a list separated by || (double pipe)

- dropdown : only for select_one / select_multiple

- checkbox: only for booleans

- hidden : hide the question

- candidateExpression : to use the candidate expression defined in the valueset

- unit::code     # code from that value set https://build.fhir.org/valueset-ucum-units.html

### parentId

used to add subItem or/and cql details
### expression

Expression can be written on several lines to clarify the sub line must refer to the parent line through the parentId column

several line with the same parentId will be joined with an OR
each set of subline is joined to the parent with an AND
only the first line may not have expression but then it must have '{{cql}}' in it in order to triger the conversion to library
##### initialExpression (optionnal)

 fhirpath/CQL code that will be executed by the api with the $populate opearation

  When writing the CQL please note:
  - all objservations (i.e. questions mapped to Observation) can be access via their label or id
  - if an Observation was assessed but not found it will return "No" ('no' coding from the custom codingsystem)
    - if an observation returns a boolean, it would be transformed to "Yes" (true) and "No" (false)
    - if an Observation returns a coding that it could take all possible value from the valueset + "No"
    - if an Observation returns a integer/quantity it could returns    integer/quantity + "No" (coding)
  - if an observation returns a coding and you want to insure it not could list the possible coding

  Cql identifier (label) must only use ascii 

##### enableWhenExpression (optionnal)

 fhirpath code that will be added on the SDC enableWhenExpression extention

##### calculatedExpression (optionnal)

fhirpath code that will be added on the SDC calculatedExpression extention

#### map_extension 
  
Will be used to implicitly flag a necessary extension. Additional information will be used to create the extension structure definition that will be referenced in the resource profile. Has the format:
  ``` 
  Path :: min :: max 
  ```
  
 - The id of the extension will be created by concatenating the path of the extension with the slice name
 - The value type of the extension will be derived from the type of the question 
 - The reference will be derived from the map_profile column
 - For the slicing name, the question label will be used
 - Min will default to 0 and max will default * unless defined otherwise
  
#### map_path 
  
THis column requires the same information that extensions need but for non extension elements. 
  ``` 
  Path :: min :: max 
  ```
  
 - The id of the element 
 - The value type of the element will be derived from the type of the question 
 - The reference will be derived from the map_profile column
 - Min will default to 0 and max will default * unless defined otherwise
  
#### map_resource
    
List of Map rules, value separeted by ||

will be use the generate map files
https://www.hl7.org/fhir/mapping-tutorial.html

the source should not be provided as the last ;

##### example

the generate
```
src.a2 as a where a2.length <= 20 -> tgt.a2 = a; // ignore it
src.a2 as a check a2.length <= 20 -> tgt.a2 = a; // error if it's longer than 20 characters
``` 
this will be needed
```
where a2.length <= 20 -> tgt.a2 = a||check a2.length <= 20 -> tgt.a2 = a
```
#### map_profile

use the create custom profiles and to create the structure map Questionnaire - Profile
the details of the profile to the mapped will be in the profile tab

#### add library:
id = {{library}}
description = [name]::[alias]::[version] e.g FHIRHelper::FHIRHelper::4.01
        version can be {{LIB_VERSION}} or {{FHIR_VERSION}} this will ne updated base on the configuration file
type = mapping 

### valueSet
maturitiy:2

this sheet define the the valuset concept that need to be defined in the project scope
the format is inpired by the pyxform 'choice' sheet

the minimal definiton is scope , valueSet and display (a code system URL), all of the concept from that codesystem will be option with {{include}} in code (to be developped, should replace url::[valueSetUrl] in the quesiton type)

the simple definition is one row per concept (those concept will be added in the custom codesystem)

Only 

but "additionnal" inforamation can be added when keyword are used in the code
- {{title}} : will set the valuesset title [display] and description [definition]
- {{exclude}}: define the code system to be excluded [definition] , the [display] can be used to set a name to link the element to be exculde (concepts to exclude will share this name in the valueSet column)
- {{include}}: define the code system to be include [definition] , the [display] can be used to set a name to link the element to be exculde (concepts to exclude will share this name in the valueSet column)
- {{choiceColumn}} : Only for candidteExpression, the choice column details will be defined as a json [definition] : {"path":".last_name", "width": "30", "forDisplay":"1"}
- {{choiceColumn}} : Only for candidteExpression, will define the URL including the query parameters
  

### cql

this sheet list the additionnal CQL required 
    
### profile

for the IG, two different profile type might be usfull
- FHIR or WHO existing profiles
- [scope] profile in case there is extention to be added to an existing profile

Defining a profile can be used also to create event, for example a QuestionnaireResponse profile can be created for a specific quesitonnaire.



Different profile will need to be generated:
- [scope] Patient
- [scope] Encounter
- [scope] Measure: to define in which conditions some measure must be done
- [scope] Conditions: either one per condition or per group of condition like "Emergency Conditions", "Mild Condition", "chronic conditon" etc
- [scope] Activity: to trigger a questionnaire (CPG collectWhith) with a task (TBC)
- [scope] task: (TBC)





## output files

the output file structure should follow the cqf-tooling structure

## Context

this tool was started to answer WHO EmCare project needs
  
## Credits
 
pyxform project
cqf-tooling project
