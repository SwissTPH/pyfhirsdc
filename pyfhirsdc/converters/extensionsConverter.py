from fhir.resources.extension import Extension
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.fhirtypes import  ExpressionType, QuantityType 
from fhir.resources.coding import Coding
from fhir.resources.fhirtypes import Canonical
from distutils.util import strtobool
import re

from pyfhirsdc.config import get_fhir_cfg
from pyfhirsdc.converters.utils import clean_name
def get_dropdown_ext():
 return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "drop-down",
                display = "Drop down")],
            text ="Drop down")
)


def get_candidate_expression_ext(desc, uri):
    if desc is not None and uri is not None:
        return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-candidateExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "application/x-fhir-query",
                expression = uri))
    else:
        return None

def get_choice_column_ext(path, label, width, for_display):
    if path is not None and label is not None:
        choice_extension = Extension(
            url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-choiceColumn",
            extension = [
                Extension( 
                    url = "path",
                    valueString = path),
                Extension(
                    url = "label",
                    valueString = label)            
            ])
        if width is not None:
            choice_extension.extension.append(Extension( 
                url = "width",
                valueQuantity = QuantityType (
                    value = width,
                    system = "http://unitsofmeasure.org",
                    code = "%"
                )))
        if for_display is not None:
            choice_extension.extension.append(Extension( 
                url = "forDisplay",
                valueBoolean = bool(strtobool(str(for_display)) )))
        return choice_extension
    else:
        return None

def get_structure_map_extension(extentions, uri):
    if extentions is None:
        extentions = []
    if  uri is not None:
        sm_ext = Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-targetStructureMap",
        valueCanonical=  Canonical(uri)
        )
        if extentions is None or len(extentions) == 0:
            return [sm_ext]
        else:
            append_unique(extentions, sm_ext, True)
    return extentions

def append_unique(extentions, new_ext, replace = False):
    nofound = True
    for ext in extentions:
        if replace and ext.url == new_ext.url:
            extentions.remove(ext)
        elif ext == new_ext:
            nofound = False
    if nofound:
        extentions.append(new_ext) 

def get_checkbox_ext():
    return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-itemControl",
    valueCodeableConcept = CodeableConcept(
            coding = [Coding( 
                system = "http://hl7.org/fhir/questionnaire-item-control",
                code = "check-box",
                display = "Check-box")],
            text ="Check-box")
    )
def get_unit_ext(unit):
    #https://www.hl7.org/fhir/ucum.html
    # value set https://build.fhir.org/valueset-ucum-units.html
    unit_part = unit.split('::')
    if len(unit_part) == 2:
        return Extension(
            url ="http://hl7.org/fhir/StructureDefinition/questionnaire-unit",
            valueCoding = Coding(
                system = "http://hl7.org/fhir/ValueSet/ucum-units",
                code = unit_part[1],

            )
        )

    
def get_hidden_ext():
    return Extension(
    url ="http://hl7.org/fhir/StructureDefinition/questionnaire-hidden",
    valueBoolean = True
    )

def convert_reference_to_firepath(expression):
    # replace value check
    expression = re.sub(pattern = r'\$\{([^}]+)\}\.(?!code)', repl = r"%resource.repeat(item).where(linkId='\1').answer.", string = expression )
    

    # other value
    return  re.sub(pattern = r'\$\{([^}]+)\}', repl = r"%resource.repeat(item).where(linkId='\1').answer.first().value", string = expression.replace('"',"'") )


def get_enable_when_expression_ext(expression, desc = None ):
  
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-enableWhenExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression)))

def get_calculated_expression_ext(expression, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression)))

def get_initial_expression_ext(expression, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/cql-expression",
                expression = convert_reference_to_firepath(expression)))

def get_initial_expression_identifier_ext(quesiton_id, desc = None ):
    return Extension(
        url ="http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-initialExpression",
        valueExpression = ExpressionType(
                description = desc,
                language = "text/cql-identifier",
                expression = clean_name(quesiton_id)))
   
def get_questionnaire_library(library):
    if not re.search("$https?\:\/\/", library):
        library = get_fhir_cfg().canonicalBase + "Library/{}".format(clean_name(library))
    return Extension(
        url ="http://hl7.org/fhir/StructureDefinition/cqf-library",
        valueCanonical  = library)
        
def add_library_extentions(resource, library):
    if resource.extension == None:
        resource.extension = []
    resource.extension.append(get_questionnaire_library(library))