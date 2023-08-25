# Custom map helpers 

## definiton

Custom map helpers must have this structure

```
def HelperName(mode, profile, question_id,df_questions,*args):
```

in the XLSX file they are called this way `HelperName::agr1||arg2 ... `


Where :

* mode:  can be docs, group or rules
** docs is used to generate the questionnnaire output docs
** group is used to generate mapping groups 
** rules is used to generate the rules that will be called in the main group for that questionnaire, those rules are used to call the group defined abovce
* profile: this is deducted from the xlsx map_profile column
* question_id: use the use the `id` column from the xlsx
* df_questions: is the questionnaire questions (aka items) dataframe (pandas)
* args*: is the agrs passed in the `map_ressource` call as depicted above


##  Misc function/helpers


### SetCommunicationRequest

create a communicaiton request
args[0] linkid for relatedPerson
runs on any none empty item answer


### SetOfficalGivenName

create Official name on a resource Ressource.name
args[0]: question ref for last name (mandatory)
args[1]: question ref first name (mandatory) 
args[2]: question ref middle name 
Applicable on any not null answer



### MapValueSetExtCode

transform a valueset to another code/codesystem
args[0]: valueset
args[1]: path to map (from valueset, map colum ex: equivalent::http://terminology.hl7.org/CodeSystem/v3-RoleCode::MTH)

Applicable on select_one


### MapWalk

enable to have shorter writting such as ressource.child1.child2=val
args[0]: pseudo mapping

## condition function/helpers


### SetCondition

create a condition, will create (clinicalStatus/verificationStatus):

* active/confirmed condition for all agree/true
* inactive/refuted condition for all disagree/false

args[x]  linkid of post-coordination under (as child) the item, can have no arg
application of boolean or agree/disagree valueset
will use the question id as condition code

### SetConditionYesNo

same a above but only valid for boolean, Deprecated

### SetConditionMultiple

create condition from a valueset of condition, will create (clinicalStatus/verificationStatus) active/unconfirmed condition for all selected, nothing for the other

arg[0] is the valuset name as defined in the valueset worksheet
applicable on select_multiple

##  Observation function/helpers

Observations helpers mostly depend on the question type 
they all create observation with value with an active status
in case it is empty or negated then the value will be false and the status inactive
by default they will use the question id as observation code

### SetObservationValueSetStr

take a string value and saved it a code with the scope cutom codesystem as system observation value


### SetObservationCodeStr
arg[0]: valueset name

take a string value to save the matching code from the referenced valueset with the scope cutom codesystem as system  as observation value


### SetObservationCode

take a select_one answer code and save it in observation value

### SetObservation/SetObservationQuatity

take a quantity answer code and save it in observation value


### SetObservationNotFound

applicable onselect_boolean 
save true is any answer is to be found 

### SetObservationYesNo

take a quantity answer code and save it with a value = true and status active if answer is true else value=false, status=inactive 


### SetObservationBoolean

deprecated

take a quantity answer code and save it with a value = true and status active if answer.code is 'yes' else value=false, status=inactive if code.code='no'


### SetObservationCodeBoolean


optionnal 3 arguments
    - arg[0] yes/true code / default question id
    - arg[1] no/false code 
    - arg[2] unknown code

Yes and No are maped like a booleans but unknown is mapped to status = 'registered' without any value


### SetObservationMultiple

take a select_one/select_multiple possible answer code and save the answer code as observation.code, with a value = true and status active if selected value=false, status=inactive if not selected


### SetObservationMultipleConcat

take a select_one/select_multiple possible answer code and save the "${question_id}&${answer.code}" as observation.code, with a value = true and status active if selected value=false, status=inactive if not selected


