# python fhir sdc generator from xls files

The goal of the project is to have tool like pyxform but for fhir structure data capture

## input files
maturitiy:0

- config.json file that define the configutation of the tool
- config/inputFile: the input xls/ods file with several mandatory shee that is use the create the contents

### config
maturitiy:0

2 sections 
- processor
- fhir



### sheets
maturitiy:1

- q.[Name] are for the questionnaire
- pd.[Name] are for the plan definiton
- valueSet are for the valueset and canditatesExpression
- profile are for the profiles/structure definitions
- cql to add cql definition to libs
- extension to define the extension to add in the profile (when linked in a question)
- carePlan (to be checked if useful)
  


### carePlan 
maturitiy:0

this sheet define the main object that contain the sdc data capture

### pd. : planDefinition
maturitiy:1

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


if the triggerType is name event then the second part is the name/url for the event (resource that implement event)

  -- to be checked if || can be use in CQL
##### example
<triggerType>::<BooleanCondition/Name>||<triggerType2>::<BooleanCondition2/Name>
-- TBC for name-event what condition  whe should have

#### definitionCanonical 
list of the definitionCanonical that need to be perfomed comma separated (canonical(ActivityDefinition | PlanDefinition | Questionnaire))

### q : Questionnaire
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
- {{choiceColumn}} : Only for candidteExpression, the choice column details will be defined as a json [definition] : {"path":".last_name", "width": "30", "forDisplay":"1"}
- {{choiceColumn}} : Only for candidteExpression, will define the URL including the query parameters
  

### cql

this sheet list the additionnal CQL required 
    


## output files

the output file structure should follow the cqf-tooling structure

## Context

this tool is started to answer WHO EmCare project needs
## Credits
 
pyxform project
cqf-tooling project
