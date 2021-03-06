from fhir.resources.extension import Extension
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.fhirtypes import  ExpressionType, QuantityType 
from fhir.resources.coding import Coding
from fhir.resources.fhirtypes import Canonical
from distutils.util import strtobool
import re
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
            nofound = True
            for ext in extentions:
                if ext.valueCanonical == uri and ext.url == "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-targetStructureMap":
                    nofound = False
            if nofound:
                extentions.append(sm_ext)
    return extentions


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

def convert_reference_to_firepath(expression):
    return re.sub(pattern = r'\$\{([^}]+)\}', repl = r"%resource.repeat(item).where(linkId='\1').answer.value", string = expression )


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
                language = "text/fhirpath",
                expression = convert_reference_to_firepath(expression)))