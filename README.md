# python fhir sdc generator from xls files

The goal of the project is to have tool like pyxform but for fhir structure data capture

## input file

the input file is an xlsx file with several mandatory sheet



### carePlan

this sheet define the main object that contain the sdc data capture

### planDefinition

this sheet defined how the questionnaires are sequences using multiple plan definition, in the cql-tooling it was based on Decision Tables

### q.<questionnaireReference>

thoses sheets are containing the questionnaires, and the required information to de the fihr mapping via structureMap (to be confirmed) and the CQL to find back the answers based on their "label"
the format is inpired by the pyxform 'survey' sheet but addapted to fhir SDC questionnaires


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