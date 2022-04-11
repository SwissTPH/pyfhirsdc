"""
Profile:http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaireresponse
Release: R4
Version: 4.0.1
"""
'Union[StrBytes, dict, Path, FHIRAbstractModel]'
from fhir.resources.questionnaireresponse import QuestionnaireResponse, QuestionnaireResponseItem
from pydantic import Field, root_validator 
from pydantic.types import StrBytes
from pathlib import Path
from fhir.resources import fhirtypes, fhirtypesvalidators
from fhir.resources.fhirabstractmodel import FHIRAbstractModel
from fhir.resources.fhirtypesvalidators import MODEL_CLASSES, fhir_model_validator
import typing
from typing import Union
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.errors import MissingError, NoneIsNotAllowedError
MODEL_CLASSES["QuestionnaireResponseSDC"] = (None, "pyfhirsdc.models.questionnaireresponseSDC")
MODEL_CLASSES["QuestionnaireResponseItemSDC"] = (None, "pyfhirsdc.models.questionnaireresponseSDC")

def questionnaireresponseitemsdc_validator(v: Union[StrBytes, dict, Path, FHIRAbstractModel]):

    return fhir_model_validator("QuestionnaireResponseItemSDC", v)


class QuestionnaireResponseItemSDCType(fhirtypes.AbstractType):
    __resource_type__ = "QuestionnaireResponseItemSDC"
    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":

        yield questionnaireresponseitemsdc_validator

class QuestionnaireResponseSDC(QuestionnaireResponse):
    #questionnaireresponse_signature: fhirtypes.SignatureType = Field(
    #    None,
    #    alias="questionnaireresponse-signature",
    #    title="A signature attesting to the content",
    #    description="Represents a wet or electronic signature for either the form overall \
    #    or for the question or item it's associated with.",
    #    # if property is element of this resource.
    #    element_property=True,
    #)
    item: typing.List[QuestionnaireResponseItemSDCType] = Field(
        None,
        alias="item",
        title="Questions and sections within the Questionnaire",
        description=(
            "A particular question, question grouping or display text that is part "
            "of the questionnaire response."
        ),
        # if property is element of this resource.
        element_property=True,
    )
    #https://github.com/nazrulworld/fhir.resources/fhir/resources/questionnaireresponse.py
    @root_validator(pre=True, allow_reuse=True)
    def questionnaireresponsesdc_validator( cls, values: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        """https://www.hl7.org/fhir/extensibility.html#Special-Case
        In some cases, implementers might find that they do not have appropriate data for
        an element with minimum cardinality = 1. In this case, the element must be present,
        but unless the resource or a profile on it has made the actual value of the primitive
        data type mandatory, it is possible to provide an extension that explains why
        the primitive value is not present.
        """
        required_fields = [("status", "status__ext")]
        _missing = object()

        def _fallback():
            return ""

        errors: typing.List["ErrorWrapper"] = []
        for name, ext in required_fields:
            field = cls.__fields__[name]
            ext_field = cls.__fields__[ext]
            value = values.get(field.alias, _missing)
            if value not in (_missing, None):
                continue
            ext_value = values.get(ext_field.alias, _missing)
            missing_ext = True
            if ext_value not in (_missing, None):
                if isinstance(ext_value, dict):
                    missing_ext = len(ext_value.get("extension", [])) == 0
                elif (
                    getattr(ext_value.__class__, "get_resource_type", _fallback)()
                    == "FHIRPrimitiveExtension"
                ):
                    if ext_value.extension and len(ext_value.extension) > 0:
                        missing_ext = False
                else:
                    validate_pass = True
                    for validator in ext_field.type_.__get_validators__():
                        try:
                            ext_value = validator(v=ext_value)
                        except ValidationError as exc:
                            errors.append(ErrorWrapper(exc, loc=ext_field.alias))
                            validate_pass = False
                    if not validate_pass:
                        continue
                    if ext_value.extension and len(ext_value.extension) > 0:
                        missing_ext = False
            if missing_ext:
                if value is _missing:
                    errors.append(ErrorWrapper(MissingError(), loc=field.alias))
                else:
                    errors.append(
                        ErrorWrapper(NoneIsNotAllowedError(), loc=field.alias)
                    )
        if len(errors) > 0:
            raise ValidationError(errors, cls)  # type: ignore

        return values
    @classmethod
    def elements_sequence(cls):
        list = QuestionnaireResponse.elements_sequence()
        
        #list.append("questionnaireresponse_signature")
        return list

  

class QuestionnaireResponseItemSDC(QuestionnaireResponseItem):
    resource_type = Field("QuestionnaireResponseItemSDC", const=True)
    #questionnaireresponse_signature: fhirtypes.SignatureType = Field(
    #    None,
    #    alias="questionnaireresponse-signature",
    #    title="A signature attesting to the content",
    #    description="Represents a wet or electronic signature for either the form overall \
    #    or for the question or item it's associated with.",
    #    # if property is element of this resource.
    #    element_property=True,
    #)
    item: typing.List[QuestionnaireResponseItemSDCType] = Field(
        None,
        alias="item",
        title="Nested questionnaire response items",
        description=(
            "Text, questions and other groups to be nested beneath a question or \
            group."
        ),
        # if property is element of this resource.
        element_property=True,
    )
    @classmethod
    def elements_sequence(cls):
        list = QuestionnaireResponseItem.elements_sequence()
        
        #list.append("questionnaireresponse_signature")
        return list


