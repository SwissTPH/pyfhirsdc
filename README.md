# Python FHIR SDC generator from XLS/ODS files

The goal of the project is to have tool like pyxform but for fhir structure data capture

## Principles of CPG/SDC encounter


## main.py option 

    -c / --conf config_file_path
    -o to generate fhir ressoruces
    -h / --help to generate this message
    -b to bundle the fhir ressource int the output path
    -l to build the library with cql in base64
    --anthro to generate the antro code system from tsv files (files can be found here https://github.com/WorldHealthOrganization/anthro/tree/master/data-raw/growthstandards)


## Input files
maturitiy:0

- config.json file that define the configutation of the tool
   see ./conf.json  

- config/inputFile: the input xls/ods file with several mandatory shee that is use the create the contents
  see ./input_example.ods (very early version for the EmCare Project)

### config
maturitiy:0

2 sections 
- processor
  - inputFile : path of the input file
  - outputPath
  - scope
  - encoding
- fhir
  - version : FHIR version
  - canonicalBase :  base url for the definiton
  - guideBase : base url for the IG
  - [RessourceName] : Fhir resource configuration
    - outputPath : where the resource output need to be saved
    - default : Default FHIR resource content in json format



### Input Sheets
maturitiy:1

- q.[Name] are for the questionnaire
- pd.[Name] are for the plan definiton
- valueSet are for the valueset and canditatesExpression
- profile are for the profiles/structure definitions
- cql to add cql definition to libs
- extension to define the extension to add in the profile (when linked in a question)
- carePlan (to be checked if useful)
- planDefinition


### CarePlan 
maturitiy:0

This sheet define the main object that contain the SDC data capture
the idea will be to create an Encounter planDefinition that will contain standardized activities

example of activities:
  - New patient
  - Danger Signs
  - measure, screening and registration
  - examination
  - treatement
  - conselling
  - follow up and planification

each activity is expected to be trigger by the L4 application (one the Encounter planDefinition will be loaded )

inside each activity, a [SDC Modular questionnaire](ttps://build.fhir.org/ig/HL7/sdc/branches/master/StructureDefinition-sdc-questionnaire-modular.html) will be linked (using [cpg-collectWith](http://hl7.org/fhir/uv/cpg/StructureDefinition-cpg-collectWith.json.html) extension )


### pd. : PlanDefinition
maturitiy:0

this sheet defined how the questionnaires are sequences using multiple plan definition, in the cql-tooling it was based on Decision Tables
#### parentActionId
<text> identifier of the parent actions 
#### id
 <text> identifier of the actions 
#### title
<text> title of the actions
#### description
<text> to describe the actions
#### applicabilityExpressions
<BooleanCondition> to define when this action is applicable
will use CQL language per default


cql function might be required to ease the code

    Patient.hasNewCondition("Nausea and vomiting")
    Patient.hasPersistentCondition( "Nausea and vomiting")


#### startExpressions
<BooleanCondition> to define when this action starts
will use CQL language per default

#### stopExpressions
<BooleanCondition> to define when this action stops
    will use CQL language per default
#### trigger
list of trigger separated by  ||
will use CQL language per default

  
#### reference
References for the particular action
  
if the triggerType is name event then the second part is the name/url for the event (resource that implement event)

  -- to be checked if || can be use in CQL
##### example
<triggerType>::<BooleanCondition/Name>||<triggerType2>::<BooleanCondition2/Name>
-- TBC for name-event what condition  whe should have

#### definitionCanonical 
list of the definitionCanonical that need to be perfomed comma separated (canonical(ActivityDefinition | PlanDefinition | Questionnaire))

### q. : Questionnaire
maturitiy:2

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
##### option
- [valueSetUrl] valueSet defined in the valueSet tab 
- url::[valueSetUrl] link to a remote value set
- candidateExpression::<x-fhir-query> will fetch the result via the <x-fhir-query>, then will dieplay the result based on the data attached to the <candidateExpressionName> in the choiceColum sheet

#### required
set to True to make sure the question is required

#### display

- dropdown : only for select_one / select_multiple

- checkbox: only for booleans

- candidateExpression : to use the candidate expression defined in the valueset


#### enableWhenExpression (optionnal)

cql (or fhirpath) code that will be added on the SDC enableWhenExpression extention

#### calculatedExpression (optionnal)

cql (or fhirpath) code that will be added on the SDC calculatedExpression extention

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


