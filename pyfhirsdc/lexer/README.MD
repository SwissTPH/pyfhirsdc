# CQL / FHIRPARSE parser / visitor

the goal is to use ANTLR visitor to update the reference to questions/observation in expression :

pyfhirsdcexpression
* [ovc]?QUOTEDIDENTIFIER ('<<'|'!<<'|'='|'!=') [ov]?QUOTEDIDENTIFIER
* [ovc]?QUOTEDIDENTIFIER (('='|'!='|'<'|'>'|'<='|'>=') literal)?



fhirpath:

* 2nd QUOTEDIDENTIFIER can be replaced by a valueset code if the content of QUOTEDIDENTIFIER is either a valueset concept id or label 
* 1st and 2nd QUOTEDIDENTIFIER by expression to get question answers or first answer
** if opperator '<<'|'!<<'|'in'|'contains' update the full expression

cql:


* 1st and 2nd QUOTEDIDENTIFIER observation, update the full expression -> 2nd QUOTEDIDENTIFIER or QUOTEDIDENTIFIER&QUOTEDIDENTIFIER = true (depending on select multiple concat or not)
* only 1st QUOTEDIDENTIFIER  observation can be replaced by obsval.QUOTEDIDENTIFIER
** 2nd QUOTEDIDENTIFIER can be replaced by a val.QUOTEDIDENTIFIER code if the content of QUOTEDIDENTIFIER is either a valueset concept id or label 

* ToInteger(pyfhirsdcexpression) -> ToInteger(Coalesce(pyfhirsdcexpression,0))



the antlr (g4) files are taken from https://cql.hl7.org/grammar.html

here are the change done:

* their content were stripped of the named subrules (#)
* QUOTEDIDENTIFIER definition was move from cql to fhirpath
* 

