/*nter"
@author: SwissTPH/SCIH/DHU
@description: This library is a core library for the SMART projects, it is used to simplify feching of observation
*/

library pyfhirsdc version '{{pyfhirsdc_version}}'

using FHIR version '4.0.1'

include FHIRHelpers version '4.0.1'

codesystem "LocationTypeCodeSystem" : 'http://terminology.hl7.org/CodeSystem/location-physical-type'
codesystem "ParticipanType" : 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType'
codesystem "ClinicalStatus" : 'http://terminology.hl7.org/CodeSystem/condition-clinical'
codesystem "VerificationStatus" :'http://terminology.hl7.org/CodeSystem/condition-ver-status'
code "Juridiction": 'jdn' from "LocationTypeCodeSystem"
code "Site": 'si' from "LocationTypeCodeSystem"
code "Attender": 'ATND'  from "ParticipanType"


code "Active": 'active' from "ClinicalStatus"


code "Unconfirmed": 'unconfirmed' from "VerificationStatus"
code "confirmed" : 'unconfirmed'from "VerificationStatus"
code "Provisional": 'provisional' from "VerificationStatus"

// the encouter id is use the retieve Observation and Condition of a given encounter
parameter "encounterid" String

parameter "cannonical_base" String

parameter "custom_code_system" String




context Patient

/*
    @param  ref FHIR.Reference the check against the encounterid Library parameter
    @return true is the reference have the same id as encounterid
*/
define function IsInEncounter(ref FHIR.Reference):
  checkReference(getEncounter, ref)


define function checkReference(R Resource, ref Reference):
    R.id = ref.id or R.id = Last(Split(ref.reference, '/'))

define function checkReference(ref1 Reference, ref2 Reference):
    ref1.id = ref2.id or ref1.id = Last(Split(ref2.reference, '/')) or ref2.id = Last(Split(ref1.reference, '/')) or ref1.reference = ref2.reference

 define "Now":
      Now()



/*
get the encounter with the id
*/
define getEncounters:
    [Encounter] E 
      where E.id = "encounterid"
        return E

define getEncounterReference:
    Reference {
      type: uri {value: 'Encounter'},
      reference: string {value:'Encounter/' + encounterid},
      id: encounterid
    }


define getPatientReference:
  Reference {
        type: uri {value: 'Patient'},
        reference: string {value:'Patient/' + Patient.id},
        id: Patient.id
      }
/*
get singleton of the encounter with the id
*/
define getEncounter:
    singleton from getEncounters

/*
Get the Encounter main Practitioner 
not compatible with R5:  individual -> actor
*/
define Practitioner:
    if getPractitionerReference is not null then First([Practitioner] p where checkReference(p,getPractitionerReference))
    else null
      
      

define getPractitionerReferences:
      getEncounter.participant p 
          where exists(p.type t where t ~ "Attender") and p.individual.type = 'Practitioner' 
          return p.individual


// we expect only one
define getPractitionerReference:
      First(getPractitionerReferences)







// *****   functions to retrieve extension define in the IG for different resources *****
/*
    @param  element Patient resource on which to look for extension
    @param  id String, id of the extension to look for
    @return List<Extension> with the right id
*/


define function GetExtensions(element DomainResource, id String):
  element.extension E
      where E.url = ("cannonical_base" + 'StructureDefinition/' + id)
      return E

/*
Get singleton of the extension with the right id (meaning the extension should not be set twice on the same resource)
    @param  element Location resource on which to look for extension
    @param  id String, id of the extension to look for
    @return Extension 
*/

define function GetExtension(element DomainResource, id String):
  singleton from GetExtensions(element, id)


/*
check if the reference have the same id as encounterid
    @param  element Condition resource on which to look for extension
    @param  postcordination List<String> list of postocoordination to look for in the extension value
    @return Boolean
*/  

define function getPostcordinationExtension(element Condition, postcordination List<String>):
  element.extension E
      where E.url = ("cannonical_base" + 'StructureDefinition/postcordination' )
      and E.value in postcordination


/*
Get usable value of the Observation in the scope of the IG
    @param  O Observation observation to get the result from
    @return (null, boolean, Code, null)
    #TODO apply concept map here
*/
define function getValue(O Observation):
  case  
      when O is null then null
      when O.value is CodeableConcept then Coalesce(First(O.value.coding C where C.system  = "custom_code_system"), First(O.value.coding))
      else O.value
  end


define function assesObservation(O Observation):
  case  
      when  O is null then null
      when  O.status in  {'cancelled'} then false
      when O.value is null then  true
      else O.value
  end


/* 
  Get the lastest observation of an encounter matching the id
    @param  id System.Code: Observation.code
    @return Observation
*/

define function GetObservationDuringEncounter(id System.Code):
      First([Observation: id ] O
        where   IsInEncounter(O.encounter) 
        and O.status in { 'final', 'amended', 'corrected','cancelled'} 
        sort by issued.value desc) 

/* 
  Get the lastest valid observation of an encounter matching the id
    @param  id System.Code: Observation.code
    @return Observation
*/

define function GetObservationDuringEncounterDone(id System.Code):
      First([Observation: id ] O
        where   IsInEncounter(O.encounter) 
        and O.status in { 'final', 'amended', 'corrected'} 
        sort by issued.value desc) 

/* 
  Get the lastest valid observation of an encounter matching the id
    @param  id System.Code: Observation.code
    @param valueCode System.Code value of the observation
    @return Observation
*/ 
define function HasObservationCodeDuringEncounterDone(id System.Code, valueCode System.Code):
    
    Exists([Observation: id ] O
        where   IsInEncounter(O.encounter) 
        and O.status in { 'final', 'amended', 'corrected'}
        and O.value is FHIR.CodeableConcept
        and O.value ~ valueCode)

/* 
  Get the lastest valid observation of an encounter matching the id
    @param  id System.Code: Observation.code
    @return Observation
*/

define function GetObservationDuringEncounterNotFound(id System.Code):
      First([Observation: id] O
       where  IsInEncounter(O.encounter) 
          and O.status in {'cancelled'}
          sort by issued.value desc)

/* 
  Get the number of valid observation of an encounter matching the id
    @param  id System.Code: Observation.code
    @return Integer
*/

define function GetNumberObservationDuringEncounter(id System.Code):
  Count(
    [Observation: id] O
        where  IsInEncounter( O.encounter) 
        and O.status in { 'final', 'amended', 'corrected'})

// ************************   GetObsValue ************************/


/* 
  Get the observation value base on observation.code
    @param  id System.Code: Observation.code
    @return (Boolean, Code, null)
*/

define function GetObsValue(id System.Code):
    getValue(GetObservationDuringEncounter(id))


/* 
  Get the observation value base on observation.code
    @param  id System.String: Observation.code.value
    @param  id System.String: Observation.code.system
    @return (Boolean, Code, null)
*/
define function GetObsValue(id System.String, codesystem System.String):
    getValue(GetObservationDuringEncounter(coding(id, codesystem)))


/* 
  Get the observation value base on observation.code from the IG system
    @param  id System.String: Observation.code.value
    @return (Boolean, Code, null)
*/
define function GetObsValue(id System.String):
    getValue(GetObservationDuringEncounter(coding(id, "custom_code_system")))


// ************************   Get Historical Observation ************************/

/* 
  Get the Historical observation not older that nbdays (encounter not used ) base on observation.code from the IG system
    @param  id System.Code: Observation.code
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/
define function GetHistoricObservation(id System.Code, nbdays Integer):
      First([Observation: id ] O
        where O.status in { 'final', 'amended', 'corrected','cancelled'} 
        and (difference in days between O.issued and Today()) < nbdays 
        sort by issued.value desc )
  //Coalesce(GetHistoricObservationDone(id ,  nbdays ),  GetHistoricObservationNotfound(id  , nbdays ))

/* 
  Get the valid Historical observation not older that nbdays (encounter not used ) base on observation.code from the IG system
    @param  id System.Code: Observation.code
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/

define function GetHistoricObservationDone(id System.Code, nbdays Integer):
      First([Observation: id ] O
        where  O.status in { 'final', 'amended', 'corrected'}
        and (difference in days between O.issued and Today()) < nbdays 
        sort by issued.value desc )

/* 
  Get the not found Historical observation not older that nbdays (encounter not used ) base on observation.code from the IG system
    @param  id System.Code: Observation.code
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/

define function GetHistoricObservationNotfound(id System.Code, nbdays Integer):
      First([Observation: id] O
        where  O.status in {'cancelled'}
          and (difference in days between O.issued and Today()) < nbdays 
        sort by issued.value desc)


// ************************   HasObsHistory ************************/

/* 
  Assess past Observation
    @param  id System.Code: Observation.code
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/
define function HasObsHistory(id System.Code, nbdays Integer):
  assesObservation(GetHistoricObservation(id, nbdays))

/* 
  Assess past Observation
    @param  id System.String: Observation.code.value
    @param  codesystem System.String: Observation.code.system
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/

define function HasObsHistory(id System.String, codesystem System.String, nbdays Integer):
  assesObservation(GetHistoricObservation(coding(id, codesystem), nbdays))

/* 
  Assess past Observation with a code from the custom_code_system
    @param  id System.String: Observation.code.value
    @param  nbdays Integer: day in the past to for
    @return (Boolean, Code, null)
*/


define function HasObsHistory(id System.String, nbdays Integer):
  assesObservation(GetHistoricObservation(coding(id), nbdays))



// ************************   Helpers ************************/


define function coding(s System.String, url System.String):
  System.Code {
                code:  s ,
                system:  url 
            }

define function coding(s FHIR.code, url System.String):
  System.Code {
                code:  s.value ,
                system:  url 
            }

//to do support url codesystem/code to SystemCode
define function coding(s System.String):
  System.Code {
                code:  s ,
                system:  "custom_code_system"
            }


define function ToUrl(s System.String):
  url {value:s}

define function ToIntC(b System.Boolean):
  case
  when b is null then 0
  when b = true then 1
  else 0
  end


// ************************   GetCond ************************/

/* 
  Get condition with a code from code
    @param  id System.String: Condition.code
    @return List<Condition>
*/


define function GetConditions(id System.Code):
      [Condition: id] O
        where  IsInEncounter( O.encounter) 
        and exists(O.verificationStatus.coding C where C.code in {'unconfirmed', 'provisional', 'differential', 'confirmed'} 
        and C.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status')
        sort by recordedDate desc


/* 
  Get condition with a code from code and given specific postcoordination
    @param  id System.String: Condition.code
    @param  postcordination List<System.String> list of pooscordination code that the Condition requirre
    @return List<Condition>
*/

   
define function GetCondition(id System.Code, postcordination List<System.String>):
    First(
      [Condition: id] C
        where  IsInEncounter( C.encounter) 
        and exists(C.verificationStatus.coding cc where cc.code in {'unconfirmed', 'provisional', 'differential', 'confirmed'} 
        and cc.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status')
        and  postcordination is null or  Count(getPostcordinationExtension(C,postcordination)) >= Count(postcordination)
        sort by recordedDate desc
    )



/*
Exctract Stem code from a ICD11 complex code strem&postcoordiniation1&postcoordiniation2...
    @param  System.String ICD11 complex code
    @return System.String stem/Condition code

*/
define function GetStemCode(id System.String):
  coding(First(Split( id, '&')))

/*
Exctract postcoordination code from a ICD11 complex code strem&postcoordiniation1&postcoordiniation2...
    @param  System.String ICD11 complex code
    @return List<System.String> postcoordination code
*/

define function GetPostcoordinationCode(id System.String):
  Tail(Split(id, '&'))

/*
Get first condition that match the code
    @param  System.Code condition code
    @return Condition
*/

define function GetCondition(id System.Code):
      First(GetConditions(id))
    
define function GetCond(id System.Code):
      First(GetConditions(id))

define function GetCond(id System.String, codesystem System.String):
  (GetCondition(coding(id, codesystem)))

define function GetCond(id System.String):
  (GetCondition(GetStemCode(id),GetPostcoordinationCode(id)))

// ************************   HasCond ************************/


define function HasCond(id System.String, codesystem System.String):
  (GetCond(coding(id, codesystem))) is not null

define function HasCond(id System.String):
  (GetCond(coding(id))) is not null

define function HasCond(id System.Code):
  (GetCond(id)) is not null

// ************************   PatientHasHistoryOfCondition ************************/




define function GetHistoricCondition(id System.Code,  nbdays Integer):
      First([Condition: id] O
        where  (difference in days between O.recordedDate and Today()) < nbdays
        and exists(O.verificationStatus.coding C where C.code in {'unconfirmed', 'provisional', 'differential', 'confirmed'} 
        and C.system = 'http://terminology.hl7.org/CodeSystem/condition-ver-status') 
        sort by recordedDate desc)



define function HasCondHistory(id System.Code, nbdays Integer):
  (GetHistoricCondition(id,  nbdays)) is not null

define function HasCondHistory(id System.String, codesystem System.String, nbdays Integer):
  (GetHistoricCondition(coding(id,codesystem),nbdays)) is not null


define function HasCondHistory(id System.String, nbdays Integer):
  (GetHistoricCondition(coding(id),  nbdays)) is not null


/*************************** Location access *******************************************/

//define function getEncounterLocationExtentsion(extention String):
//    getExtentionFromLocations(getEncounter.location, extention)

//define function getExtentionFromLocations(locations List<FHIR.Encounter.Location>, extention String):
//  if Count(locations) = 1 then getExtentionFromLocationHiearchy(getExtentionFromLocationReference(First(locations).location), extention)
//  else Coalesce(getExtentionFromLocationHiearchy(getExtentionFromLocationReference(First(locations).location), extention), getExtentionFromLocations(Tail(locations), extention String))


define function getExtentionFromLocationReference(ref Reference):
    First([Location] l where l.id = ref.id or l.id = Last(Split(ref.reference, '/')))



/*
function that get the intersection of the location managed by the ServiceProvider and part of the encounter as Site physicalType, Encounter location can be ingnored

*/
define getEncounterJuridiction:
    First(
      [Location] l 
        where  Exists(
          getEncounter.location el where el.physicalType ~ "Juridiction" and checkReference(l,el.location) 
        ))
    
define getEncounterServiceProvider:
    First([Organization] O where checkReference(O, getEncounter.serviceProvider))

define getEncouterSite:
     First(
      [Location] l 
        where  Exists(
          getEncounter.location el where el.physicalType ~ "Site" and checkReference(l,el.location) 
        )) 

/*
find the service provided at the site by the same healtcareprovider

*/

define getEncouterSiteHealthCareService:
      [HealthcareService] H 
        where Exists( H.location l where checkReference(getEncouterSite,l) )

define getEncounterServiceProviderHealthCareService:
      [HealthcareService] H 
        where Exists( H.location l where checkReference(getEncouterSite,l) )
        and checkReference(getEncounter.serviceProvider,H.providedBy)

define "EmCare.B23.DE32a":
   true

define "EmCare.B23.DE32b":
    true

define "getPostCordination_EmCare.B23.DE32":
    if "EmCare.B23.DE32a" then { Extension {
        url : uri {value: 'https://fhir.dk.swisstph-mis.ch/matchbox/fhir/StructureDefinition/postcoordination'},
        value: FHIR.CodeableConcept {coding: { FHIR.Coding { system: FHIR.uri { value : 'https://fhir.dk.swisstph-mis.ch/matchbox/fhir/CodeSystem/che-custom-codes' }, code: FHIR.code {value: 'EmCare.B23.DE32a' } } } }
    } }
    else null
    |
    if "EmCare.B23.DE32b" then { Extension {
        url : uri {value: 'https://fhir.dk.swisstph-mis.ch/matchbox/fhir/StructureDefinition/postcoordination'},
        value: FHIR.CodeableConcept {coding: { FHIR.Coding { system: FHIR.uri { value : 'https://fhir.dk.swisstph-mis.ch/matchbox/fhir/CodeSystem/che-custom-codes' }, code: FHIR.code {value: 'EmCare.B23.DE32b' } } } }
    } }
    else null
